import socket
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.schemas.sip import Patron, Item, HoldDetails, SIPInfo

class SIPClient:
    """
    SIP2 (Standard Interchange Protocol) Client Implementation
    Workflow: request -> connect socket -> build msg -> login -> send request -> filter response -> return response
    """
    
    REQUEST_COUNTER = 0
    
    def __init__(self):
        self.client_socket: Optional[socket.socket] = None
        self.sip_host: str = ""
        self.sip_port: int = 0
        self.sip_user: str = ""
        self.sip_password: str = ""
        self.loc_id: str = ""
        self.lib_id: str = ""
    
    def initialize(self, sip_info: SIPInfo):
        """Initialize SIP client with connection details"""
        self.sip_host = sip_info.host
        self.sip_port = int(sip_info.port)
        self.sip_user = sip_info.user
        self.sip_password = sip_info.password
        self.loc_id = sip_info.loccd
        self.lib_id = sip_info.libid
    
    def connect(self) -> bool:
        """Step 1: Connect to SIP server"""
        try:
            if self.client_socket and self.is_connected():
                self.disconnect()
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(2)  # Set a reasonable timeout for connection

            # Set socket options for clean disconnection
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            self.client_socket.connect((self.sip_host, self.sip_port))
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from SIP server with careful cleanup"""
        try:
            if self.client_socket:
                try:
                    # Drain any lingering data before shutdown
                    self._drain_socket()
                    
                    # Gracefully shutdown the socket connection
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except (OSError, socket.error) as e:
                    # Socket might already be disconnected (ENOTCONN)
                    print(f"Socket shutdown info: {e}")
                finally:
                    # Always close the socket
                    try:
                        self.client_socket.close()
                    except Exception as e:
                        print(f"Socket close error: {e}")
                    finally:
                        # Clear the socket reference
                        self.client_socket = None
        except Exception as e:
            print(f"Disconnect error: {e}")
            self.client_socket = None
    
    def is_connected(self) -> bool:
        """Check if socket is connected"""
        try:
            if not self.client_socket:
                return False
            # Try to check connection status
            self.client_socket.getpeername()
            return True
        except:
            return False
    
    def _drain_socket(self):
        """Drain any lingering data from socket"""
        try:
            if not self.client_socket or not self.is_connected():
                return
            
            # Use non-blocking mode for efficient draining
            self.client_socket.setblocking(False)
            try:
                while True:
                    try:
                        data = self.client_socket.recv(4096)
                        if not data:
                            break
                    except (BlockingIOError, socket.error):
                        break
            finally:
                self.client_socket.setblocking(True)  # Reset to blocking mode
        except Exception as e:
            print(f"Socket drain error: {e}")
    
    def calculate_checksum(self, data: str) -> str:
        """Step 2b: Calculate SIP2 checksum"""
        checksum = 0
        for char in data:
            checksum += ord(char)
        checksum &= 0xffff
        checksum = 65536 - checksum
        return f"{checksum:04X}"
    
    def get_request_sequence(self) -> str:
        """Generate request sequence number"""
        SIPClient.REQUEST_COUNTER = (SIPClient.REQUEST_COUNTER + 1) % 10
        return str(SIPClient.REQUEST_COUNTER)
    
    def build_and_send_message(self, message: str) -> str:
        """
        Step 2: Build message with sequence and checksum
        Step 3a: Send request
        Step 3b: Receive response - optimized for fast response
        """
        try:
            sequence = self.get_request_sequence()
            message = f"{message}|AY{sequence}AZ"
            checksum = self.calculate_checksum(message)
            final_message = f"{message}{checksum}\r"
            print(f"Final SIP message to send: {final_message.strip()}")
            # Send message without delay - start receiving immediately
            self.client_socket.send(final_message.encode('utf-8'))
            
            # Receive response - SIP messages end with \r
            response_data = b""

            response_data = self.client_socket.recv(4096)
            print(f"Raw response data: {response_data}")
            response = response_data.decode('utf-8', errors='ignore').strip()
            print(f"Parsed response: {response}")
            return response
        except Exception as e:
            print(f"Send/Receive error: {e}")
            return ""
    
    def get_string_part(self, message: str, token: str) -> str:
        """Step 4: Parse response to extract field values"""
        try:
            if token not in message:
                return ""
            start_idx = message.index(token) + len(token)
            end_idx = message.find("|", start_idx)
            if end_idx == -1:
                end_idx = len(message)
            return message[start_idx:end_idx]
        except:
            return ""
    
    def login(self) -> bool:
        """Step 2: Login to SIP server"""
        try:
            message = f"9300CN{self.sip_user}|CO{self.sip_password}"
            response = self.build_and_send_message(message)
            
            if len(response) > 5 and response[2] == "1":
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_patron(self, patron_id: str, pin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get patron information
        Workflow: connect -> login -> send patron request -> parse response
        """
        response = {
            "status": "failed",
            "message": "SIP2 connection failed",
            "patron": None,
            "issueditems": []
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return response
            
            # Login
            if not self.login():
                response["message"] = "SIP2 Login failed"
                return response
            # Build patron status message (63 - Patron Status Request)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            
            if pin:
                msg = f"63001{timestamp}  Y       AO|AA{patron_id}|AC|AD{pin}"
            else:
                msg = f"63001{timestamp}  Y       AO|AA{patron_id}|AC"
            
            result = self.build_and_send_message(msg)
            
            if len(result) < 2:
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Response code 64 = Patron Status Response
            if result[0:2] != "64":
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Check if patron was found
            patron_name = self.get_string_part(result, "|AE")
            if not patron_name:
                response["message"] = self.get_string_part(result, "|AF")
                response["status"] = "fail"
                return response
            
            # Parse patron information
            patron = Patron(
                patronid=self.get_string_part(result, "|AA"),
                name=patron_name,
                email=self.get_string_part(result, "|BE") or None,
                contactno=self.get_string_part(result, "|BF") or None,
                fine=float(self.get_string_part(result, "|BV") or 0),
                isvalid=self.get_string_part(result, "|BL") or "NA",
                isvalidpwd=self.get_string_part(result, "|CQ") or "NA"
            )
            
            # Extract patron item counts
            if len(result) >= 45:
                try:
                    patron.issueditems = int(result[45:49])
                    patron.holditems = int(result[37:41])
                    patron.overdueitems = int(result[41:45])
                except:
                    pass
            
            # Get issued items
            issued_items = self._parse_issued_items(result)
            
            response["status"] = "success"
            response["patron"] = patron.dict(exclude_none=True)
            response["issueditems"] = [item.dict(exclude_none=True) for item in issued_items]
            response["message"] = self.get_string_part(result, "|AF")
            
            return response
            
        except Exception as e:
            response["message"] = str(e)
            return response
        finally:
            self.disconnect()
    
    def _parse_issued_items(self, message: str) -> List[Item]:
        """Parse issued items from patron status response"""
        items = []
        temp_msg = message
        
        while "AU" in temp_msg:
            try:
                start = temp_msg.index("AU") + 2
                end = temp_msg.find("|", start)
                if end == -1:
                    end = len(temp_msg)
                
                item_id = temp_msg[start:end]
                if item_id:
                    item = self._get_item_details(item_id)
                    if item and item.title:
                        items.append(item)
                
                temp_msg = temp_msg[end:]
            except:
                break
        
        return items
    
    def _get_item_details(self, item_id: str) -> Optional[Item]:
        """Get item details using item status request"""
        try:
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            msg = f"17{timestamp}AO|AB{item_id}"
            
            result = self.build_and_send_message(msg)
            
            # Response code 18 = Item Information Response
            if len(result) >= 2 and result[0:2] == "18":
                item = Item(
                    itemid=item_id,
                    title=self.get_string_part(result, "|AJ"),
                    duedate=self.get_string_part(result, "|AH") or None
                )
                return item
            return None
        except:
            return None
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """
        Get item information
        Workflow: connect -> login -> send item request -> parse response
        """
        response = {
            "status": "failed",
            "message": "SIP2 connection failed",
            "itemid": item_id,
            "title": None,
            "statuscd": None,
            "itemstatus": None
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return response
            
            # Login
            if not self.login():
                response["message"] = "SIP2 Login failed"
                return response
            
            # Send item status request (17)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            msg = f"17{timestamp}AO|AB{item_id}"
            
            result = self.build_and_send_message(msg)
            
            if len(result) < 2:
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Response code 18 = Item Information Response
            if result[0:2] != "18":
                response["message"] = "Invalid response from SIP2"
                return response
            
            title = self.get_string_part(result, "|AJ")
            if not title:
                response["status"] = "fail"
                response["message"] = self.get_string_part(result, "|AF")
                return response
            print(f"T - {(result[2:4])}")
            print(f"T - {int(result[2:4])}")
            print(f"T - {int(result[2:4]) if len(result) >= 4 else 0}")
            response["status"] = "success"
            response["title"] = title
            response["statuscd"] = result[2:4] if len(result) >= 4 else ""
            response["itemstatus"] = self._circulation_status(int(result[2:4]) if len(result) >= 4 else 0)
            response["message"] = self.get_string_part(result, "|AF")
            
            return response
            
        except Exception as e:
            response["message"] = str(e)
            return response
        finally:
            self.disconnect()
    
    def checkout(self, patron_id: str, item_id: str, pin: Optional[str] = None) -> Dict[str, Any]:
        """
        Checkout item
        Workflow: connect -> login -> send checkout request -> parse response
        """
        response = {
            "status": "failed",
            "message": "SIP2 connection failed",
            "txnstatus": None,
            "patron": None,
            "item": None
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return response
            
            # Login
            if not self.login():
                response["message"] = "SIP2 Login failed"
                return response
            
            # Send checkout request (11)
            now = datetime.now()
            due_date = (now + timedelta(days=15)).strftime("%Y%m%d    000000")
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            msg = f"11NN{timestamp}{due_date}AO|AA{patron_id}|AB{item_id}|AC"
            
            result = self.build_and_send_message(msg)
            
            if len(result) < 2:
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Response code 12 = Checkout Response
            if result[0:2] != "12":
                response["message"] = "Invalid response from SIP2"
                response["status"] = "fail"
                return response
            
            response["status"] = "success"
            response["txnstatus"] = "success" if (len(result) > 2 and result[2] == "1") else "fail"
            response["item"] = Item(itemid=item_id).dict(exclude_none=True)
            response["patron"] = Patron(patronid=patron_id).dict(exclude_none=True)
            response["message"] = self.get_string_part(result, "|AF")
            
            return response
            
        except Exception as e:
            response["message"] = str(e)
            return response
        finally:
            self.disconnect()
    
    def checkin(self, item_id: str) -> Dict[str, Any]:
        """
        Checkin item
        Workflow: connect -> login -> send checkin request -> parse response
        """
        response = {
            "status": "failed",
            "message": "SIP2 connection failed",
            "txnstatus": None,
            "item": None,
            "patron": None,
            "hold": None
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return response
            
            # Login
            if not self.login():
                response["message"] = "SIP2 Login failed"
                return response
            
            # Send checkin request (09)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            msg = f"09N{timestamp}{timestamp}AP|AO|AB{item_id}|AC"
            
            result = self.build_and_send_message(msg)
            
            if len(result) < 2:
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Response code 10 = Checkin Response
            if result[0:2] != "10":
                response["message"] = "Invalid response from SIP2"
                response["status"] = "fail"
                return response
            
            response["status"] = "success"
            response["item"] = Item(itemid=item_id).dict(exclude_none=True)
            response["txnstatus"] = "success" if (len(result) > 2 and result[2] == "1") else "fail"
            
            # Parse hold information if present
            hold_patron_id = self.get_string_part(result, "|CY")
            if hold_patron_id:
                response["hold"] = {
                    "patronid": hold_patron_id,
                    "libraryid": self.get_string_part(result, "|CT"),
                    "details": self.get_string_part(result, "|DA")
                }
                response["patron"] = Patron(patronid=hold_patron_id).dict(exclude_none=True)
            
            response["message"] = self.get_string_part(result, "|AF")
            
            return response
            
        except Exception as e:
            response["message"] = str(e)
            return response
        finally:
            self.disconnect()
    
    def renew(self, patron_id: str, item_id: str, pin: Optional[str] = None) -> Dict[str, Any]:
        """
        Renew item
        Workflow: connect -> login -> send renew request -> parse response
        """
        response = {
            "status": "failed",
            "message": "SIP2 connection failed",
            "txnstatus": None,
            "patron": None,
            "item": None
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return response
            
            # Login
            if not self.login():
                response["message"] = "SIP2 Login failed"
                return response
            
            # Send renew request (29)
            now = datetime.now()
            due_date = (now + timedelta(days=15)).strftime("%Y%m%d    000000")
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            msg = f"29YY{timestamp}{due_date}AO|AA{patron_id}|AB{item_id}|AC"
            
            result = self.build_and_send_message(msg)
            
            if len(result) < 2:
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Response code 30 = Renew Response
            if result[0:2] != "30":
                response["message"] = "Invalid response from SIP2"
                response["status"] = "fail"
                return response
            
            response["status"] = "success"
            response["txnstatus"] = "success" if (len(result) > 2 and result[2] == "1") else "fail"
            response["item"] = Item(itemid=item_id).dict(exclude_none=True)
            response["patron"] = Patron(patronid=patron_id).dict(exclude_none=True)
            response["message"] = self.get_string_part(result, "|AF")
            
            return response
            
        except Exception as e:
            response["message"] = str(e)
            return response
        finally:
            self.disconnect()
    
    def reserve(self, patron_id: str, item_id: str, pin: Optional[str] = None) -> Dict[str, Any]:
        """
        Reserve item
        Workflow: connect -> login -> send reserve request -> parse response
        """
        response = {
            "status": "failed",
            "message": "SIP2 connection failed",
            "txnstatus": None,
            "patron": None,
            "item": None
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return response
            
            # Login
            if not self.login():
                response["message"] = "SIP2 Login failed"
                return response
            
            # Send reserve request (15)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            msg = f"15+{timestamp}{timestamp}|BY2|AO|AA{patron_id}|AB{item_id}|AC"
            
            result = self.build_and_send_message(msg)
            
            if len(result) < 2:
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Response code 16 = Reserve Response
            if result[0:2] != "16":
                response["message"] = "Invalid response from SIP2"
                response["status"] = "fail"
                return response
            
            response["status"] = "success"
            response["txnstatus"] = "success" if (len(result) > 2 and result[2] == "1") else "fail"
            response["item"] = Item(itemid=item_id).dict(exclude_none=True)
            response["patron"] = Patron(patronid=patron_id).dict(exclude_none=True)
            response["message"] = self.get_string_part(result, "|AF")
            
            return response
            
        except Exception as e:
            response["message"] = str(e)
            return response
        finally:
            self.disconnect()
    
    def pay_fine(self, patron_id: str, amount: float, 
                 finetype: str = "01", paymentmode: str = "00", txnid: str = "") -> Dict[str, Any]:
        """
        Pay fine
        Workflow: connect -> login -> send fine payment request -> parse response
        """
        response = {
            "status": "failed",
            "message": "SIP2 connection failed"
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return response
            
            # Login
            if not self.login():
                response["message"] = "SIP2 Login failed"
                return response
            
            # Send fine payment request (37)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d    %H%M%S")
            msg = f"37{timestamp}{finetype}{paymentmode}INRBV{amount}|AO|AA{patron_id}|BK{txnid}"
            
            result = self.build_and_send_message(msg)
            
            if len(result) < 2:
                response["message"] = "Invalid response from SIP2"
                return response
            
            # Response code 38 = Fine Payment Response
            if result[0:2] != "38":
                response["message"] = "Invalid response from SIP2"
                response["status"] = "fail"
                return response
            
            response["status"] = "success" if (len(result) > 2 and result[2] == "Y") else "fail"
            response["message"] = self.get_string_part(result, "|AF")
            
            return response
            
        except Exception as e:
            response["message"] = str(e)
            return response
        finally:
            self.disconnect()
    
    @staticmethod
    def _circulation_status(code: int) -> str:
        """Map circulation status code to description"""
        status_map = {
            2: "On order",
            3: "Title not issued",
            4: "Already issued",
            5: "Charged; Not to be recalled until earliest recall date",
            6: "In process",
            7: "Recalled",
            8: "Waiting on hold shelf",
            9: "Waiting to be re-shelved",
            10: "In transit between library locations",
            11: "Claimed returned",
            12: "Lost",
            13: "Missing"
        }
        return status_map.get(code, "Unknown")
