import requests
import json


class ZarinPalSandbox:
    _payment_request_url = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    _payment_verify_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    _payment_page_url = "https://sandbox.zarinpal.com/pg/StartPay/"
    _callback_url = "http://redreseller.com/verify"

    def __init__(self, merchant_id):
        self.merchant_id = merchant_id

    def payment_request(self, amount, description="پرداختی کاربر", **kwargs):
        payload = {
            "merchant_id": self.merchant_id,
            "amount": str(amount),
            "callback_url": self._callback_url,
            "description": description,
            "metadata": {
                "mobile": "09195523234",
                "email": "info.davari@gmail.com"
            }
            }
        headers = {
            'Content-Type': 'application/json'
            }

        response = requests.request("POST", self._payment_request_url, headers=headers, data=json.dumps(payload))
        return response
    


    def payment_verify(self,amount,authority):
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(self._payment_verify_url, headers=headers, data=json.dumps(payload))
        return response.json()

    def generate_payment_url(self,authority):
        return self._payment_page_url + authority



if __name__ == "__main__":
    zarinpal = ZarinPalSandbox(merchant_id="4ced0a1e-4ad8-2311-9668-3ea3ae8e8897")
    response =zarinpal.payment_request(15000)
    response_dict = json.loads(response.text)
    print(response_dict)
    
    input("proceed to generating payment url?")
    
    print(zarinpal.generate_payment_url(response_dict["data"]["authority"]))
    
    input("check the payment?")
    
    response = zarinpal.payment_verify(15000,response_dict["data"]["authority"])
    print(response)
    
    