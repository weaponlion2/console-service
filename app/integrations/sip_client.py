class SIPClient:

    def patron(self, payload):
        return {
            "issueditems": [],
            "message": "Mock SIP Patron",
            "patron": {
                "name": "Test User",
                "patronid": payload["patronid"],
                "isvalid": "Y",
                "isvalidpwd": "Y",
                "email": "",
                "contactno": "",
                "fine": 0
            },
            "status": "success"
        }

    def item(self, payload):
        return {
            "itemid": payload["itemid"],
            "itemstatus": "Title not issued",
            "statuscd": "03",
            "message": "",
            "status": "success",
            "title": "Sample Book"
        }

    def checkout(self, payload):
        return {"status": "success", "txnstatus": "success"}

    def checkin(self, payload):
        return {"status": "success", "txnstatus": "success"}
