import requests
import random
from flask import Flask, jsonify, request
import json
import os
import base64
import hashlib
from datetime import datetime, timedelta

class GameInfo:
    def __init__(self):
        self.TitleId: str = "DF2F4"
        self.SecretKey: str = "UCAKYJEFJJ4GHS74ZK8FC14CFSTQG5TBXBFXBCJH5KUBBDR3A4"
        self.aApiKey: str = "OC|9835875326522978|dba3cebc394f5dc975e184362896135d"

    def get_auth_headers(self):
        return {"content-type": "application/json", "X-SecretKey": self.SecretKey}


settings = GameInfo()
app = Flask(__name__)

item_names = [ # put bxt in credits (these are itbxts taht switch around on daily tee)
    "LBAEY.", "LBAFH.", "LBAFA.", "LBAFB.", "LBAFC.", "LBAFD.", "LBAFE.", "LBAFF.", "LBAFG.", "LBAEZ.", "LBAFP.", "LBAFQ.", "LBAFR.", "LBAEX.", "LBAGJ." # put bxt in credits
] # put bxt in credits

@app.route("/api/PlayFabAuthentication", methods=["POST", "GET"])
def PlayFabAuthentication():
    if request.method != "POST":
        return "", 404
        
    rjson = request.get_json()
    oculus_id = rjson.get("OculusId")
    nonce = rjson.get("Nonce")

    print(rjson)
        
    oculus_response = requests.post("https://graph.oculus.com/user_nonce_validate", json={
        "access_token": f"{settings.ApiKey}",
        "nonce": nonce,
        "user_id": oculus_id
    }) 

    if oculus_response.status_code != 200 or not oculus_response.json().get("is_valid", False):
        return jsonify({"BanMessage": "Your account has been traced and you have been banned.", "BanExpirationTime": "Indefinite"}), 403

    login_req = requests.post(
        url = f"https://{settings.TitleId}.playfabapi.com/Server/LoginWithServerCustomId",
        json = {
            "ServerCustomId": "OCULUS" + oculus_id,
            "CreateAccount": True
        },
        headers=settings.get_auth_headers()
    )

    if login_req.status_code == 200:
        return jsonify({
            "SessionTicket": login_req.json().get("data").get("SessionTicket"),
            "EntityToken": login_req.json().get("data").get("EntityToken").get("EntityToken"),
            "PlayFabId": login_req.json().get("data").get("PlayFabId"),
            "EntityId": login_req.json().get("data").get("EntityToken").get("Entity").get("Id"),
            "EntityType": login_req.json().get("data").get("EntityToken").get("Entity").get("Type"),
            "AccountCreationIsoTimestamp": datetime.fromisoformat(requests.post(f"https://{settings.TitleId}.playfabapi.com/Server/GetPlayerProfile",json={"PlayFabId": login_req.json().get("data").get("PlayFabId"), "ProfileConstraints": {"ShowCreated": True}},headers=settings.get_auth_headers()).json()["data"]["PlayerProfile"]["Created"].replace("Z", "+00:00")).strftime("%Y-%m-%dT%H:%M:%S")
        }), 200
    else: 
        ban_info = login_req.json()
        if ban_info.get("errorCode") == 1002:
            ban_message = ban_info.get("errorMessage")
            ban_details = ban_info.get("errorDetails")
            ban_expiration_key = next(iter(ban_details.keys()), None)
            ban_expiration_list = ban_details.get(ban_expiration_key, [])
            ban_expiration = (
                ban_expiration_list[0]
                if len(ban_expiration_list) > 0
                else "Indefinite"
            )
            print(f"Banned for: {ban_expiration_key}")
            print(f"Banned until: {ban_expiration}")
            
            return jsonify({
                "BanMessage": ban_expiration_key,
                "BanExpirationTime": ban_expiration,
            }), 403

@app.route("/api/MothershipAuthentication", methods=["POST"])
def mothership_auth():
    datp = request.get_json()

    CustomId = datp.get("CustomId", "null")
    PlayFabId = datp.get("PlayFabId", "null")
    GameMode = datp.get("GameMode", "DefaultMode")
    DeviceType = datp.get("Device", "Unknown")
    Region = datp.get("Region", "global")

    MetaLog = {
        "CustomId": CustomId,
        "PlayFabId": PlayFabId,
        "GameMode": GameMode,
        "Device": DeviceType,
        "Region": Region
    }

    login = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/LoginWithServerCustomId",
        json={
            "CustomId": CustomId,
            "CreateAccount": False
        },
        headers={
            "Content-Type": "application/json",
            "X-SecretKey": dash
        }
    )

    if login.status_code != 200:
        if login.status_code == 403:
            ban_info = login.json()
            if ban_info.get('errorCode') == 1002:
                ban_message = ban_info.get('errorMessage', "No ban message provided.")
                ban_details = ban_info.get('errorDetails', {})
                ban_expiration_key = next(iter(ban_details.keys()), None)
                ban_expiration_list = ban_details.get(ban_expiration_key, [])
                ban_expiration = ban_expiration_list[0] if len(ban_expiration_list) > 0 else "No expiration date provided."

                print(f"[BAN DETECTED] {MetaLog}")

                return jsonify({
                    'BanReason': ban_expiration_key,
                    'BanExpiration': ban_expiration,
                    'Region': Region,
                    'GameMode': GameMode
                }), 403
            else:
                return jsonify({
                    'Error': 'Forbidden',
                    'Message': ban_info.get('errorMessage', 'Unknown reason'),
                    'Meta': MetaLog
                }), 403
        else:
            return jsonify({
                'Error': 'PlayFab Login Error',
                'Message': login.json().get('errorMessage', 'Unknown error'),
                'Meta': MetaLog
            }), login.status_code

    link = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/LinkServerCustomId",
        json={
            "PlayFabId": PlayFabId,
            "ServerCustomId": CustomId,
            "ForceLink": True
        },
        headers={
            "Content-Type": "application/json",
            "X-SecretKey": dash
        }
    )

    if link.status_code != 200:
        return jsonify({
            "status": "error",
            "step": "LinkServerCustomId",
            "code": link.status_code,
            "error": link.text,
            "meta": MetaLog
        }), link.status_code

    services = {
        "CosmeticsSync": True,
        "FriendsInit": True,
        "GuildSync": False,
        "SeasonalEvents": True
    }

    return jsonify({
        "status": "success",
        "GameMode": GameMode,
        "Region": Region,
        "Device": DeviceType,
        "loginData": login.json(),
        "linkData": link.json(),
        "servicesInitialized": services,
        "meta": MetaLog
    })



@app.route("/api/CachePlayFabId", methods=["POST"])
def cache_playfab_id():
    return jsonify({"Message": "Success"}), 200
    
@app.route("/", methods=["POST", "GET"])
def title_data():
    response = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/GetTitleData",
        headers=settings.get_auth_headers()
    )

    if response.status_code == 200:
        return jsonify(response.json().get("data").get("Data"))
    else:
        return jsonify({}), response.status_code


polls = [ # CREDITS TO S4GE, DISCORD.GG/S4GE
    {"id": 1, "question": "IS COSMO SIGMA??", "options": ["YES", "NO"], "votes": [0, 0], "predictions": [0, 0], "active": True},
    {"id": 2, "question": "PREVIOUS VOTE", "options": ["YES", "NO"], "votes": [999, 999], "predictions": [111, 111], "active": False}
]

@app.route("/api/FetchPoll", methods=["POST"]) # CREDITS TO S4GE, DISCORD.GG/S4GE
def fetch_poll():
    logger.info("[POLL] Fetch polls request")
    return jsonify(polls), 200

@app.route("/api/SubmitVote", methods=["POST"]) # CREDITS TO S4GE, DISCORD.GG/S4GE
def submit_vote():
    payload = request.get_json() or {}
    poll_id = payload.get("PollId")
    user = payload.get("PlayFabId")
    choice = payload.get("OptionIndex")
    prediction = payload.get("IsPrediction")

    poll = next((p for p in polls if p["id"] == poll_id), None)
    if not poll or not poll["active"] or choice not in range(len(poll["options"])):
        logger.error("[POLL] Invalid vote attempt: poll %s, choice %s", poll_id, choice)
        return jsonify({"status": "error", "message": "Invalid poll or option."}), 400

    key = "predictions" if prediction else "votes"
    poll[key][choice] += 1
    logger.info("[POLL] Updated %s for user %s on poll %s", key, user, poll_id)

    return jsonify({
        "status": "success",
        "pollId": poll_id,
        "option": poll["options"][choice],
        "newCount": poll[key][choice]
    }), 200


@app.route("/api/ConsumeOculusIAP", methods=["POST"])
def consume_oculus_iap():
    rjson = request.get_json()

    access_token = rjson.get("userToken")
    user_id = rjson.get("userID")
    nonce = rjson.get("nonce")
    sku = rjson.get("sku")

    response = requests.post(
        url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={user_id}&sku={sku}&access_token={settings.ApiKey}",
        headers={"content-type": "application/json"},
    )

    if response.json().get("success"):
        return jsonify({"result": True})
    else:
        return jsonify({"error": True})

@app.route("/api/GetAcceptedAgreements", methods=['POST', 'GET'])
def GetAcceptedAgreements():
  data = request.json

  return jsonify({"PrivacyPolicy":"1.1.28","TOS":"11.05.22.2"}), 200

@app.route("/api/SubmitAcceptedAgreements", methods=['POST', 'GET'])
def SubmitAcceptedAgreements():
  data = request.json

  return jsonify({}), 200

@app.route("/api/ConsumeCodeItem", methods=["POST"])
def consume_code_item():
    rjson = request.get_json()
    code = rjson.get("itemGUID")
    playfab_id = rjson.get("playFabID")
    session_ticket = rjson.get("playFabSessionTicket")

    if not all([code, playfab_id, session_ticket]):
        return jsonify({"error": "Missing parameters"}), 400

    raw_url = f"https://github.com/redapplegtag/backendsfrr" # make a github and put the raw here (Redeemed = not redeemed, u have to add discord webhookss and if your smart you can make it so it auto updates the github url (redeemed is not redeemed, AlreadyRedeemed is already redeemed, then dats it
    # code:Redeemed 
    response = requests.get(raw_url)

    if response.status_code != 200:
        return jsonify({"error": "GitHub fetch failed"}), 500

    lines = response.text.splitlines()
    codes = {split[0].strip(): split[1].strip() for line in lines if (split := line.split(":")) and len(split) == 2}

    if code not in codes:
        return jsonify({"result": "CodeInvalid"}), 404

    if codes[code] == "AlreadyRedeemed":
        return jsonify({"result": codes[code]}), 200

    grant_response = requests.post(
        f"https://{settings.TitleId}.playfabapi.com/Admin/GrantItemsToUsers",
        json={
            "ItemGrants": [
                {
                    "PlayFabId": playfab_id,
                    "ItemId": item_id,
                    "CatalogVersion": "DLC"
                } for item_id in ["dis da cosmetics", "anotehr cposmetic", "anotehr"]
            ]
        },
        headers=settings.get_auth_headers()
    )


    if grant_response.status_code != 200:
        return jsonify({"result": "PlayFabError", "errorMessage": grant_response.json().get("errorMessage", "Grant failed")}), 500

    new_lines = [f"{split[0].strip()}:AlreadyRedeemed" if split[0].strip() == code else line.strip() 
             for line in lines if (split := line.split(":")) and len(split) >= 2]

    updated_content = "\n".join(new_lines).strip()

    return jsonify({"result": "Success", "itemID": code, "playFabItemName": codes[code]}), 200

@app.route('/api/v2/GetName', methods=['POST', 'GET'])
def GetNameIg():
    return jsonify({"result": f"GORILLA{random.randint(1000,9999)}"})

@app.route("/api/TryDistributeCurrencyV2", methods=["POST"])
def TryDistributeCurrencyV2():
    if request.method != "POST":
        return "", 404
        
    rjson = request.json
    sr_a_day = 100
    current_player_id = rjson.get("CallerEntityProfile", {}).get("Lineage", {}).get("MasterPlayerAccountId")

    get_data_response = requests.post(
        f"https://{settings.TitleId}.playfabapi.com/Server/GetUserReadOnlyData",
        headers=settings.get_auth_headers(),
        json={
            "PlayFabId": current_player_id,
            "Keys": ["DailyLogin"]
        }
    )

    daily_login_value = get_data_response.json().get("data").get("Data").get("DailyLogin", {}).get("Value", None)

    last_login_date = None
    if daily_login_value:
        last_login_date = datetime.fromisoformat(daily_login_value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    if not last_login_date or last_login_date < datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc):
        requests.post(
            f"https://{settings.TitleId}.playfabapi.com/Server/AddUserVirtualCurrency",
            headers=settings.get_auth_headers(),
            json={
                "PlayFabId": current_player_id,
                "VirtualCurrency": "SR",
                "Amount": sr_a_day
            }
        )

        requests.post(
            f"https://{settings.TitleId}.playfabapi.com/Server/UpdateUserReadOnlyData",
            headers=settings.get_auth_headers(),
            json={
                "PlayFabId": current_player_id,
                "Data": {
                    "DailyLogin": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc).isoformat()
                }
            }
        )

    return "", 200

@app.route("/api/K-ID", methods=["POST"])
def k_id():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    required_fields = ["Age", "Permissions", "GetSubmittedAge", "VoiceChat", "CustomNames", "PhotonPermission"]
    missing = [field for field in required_fields if field not in data]
    if missing:
      return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400


    user_age = data.get("Age")
    permissions = data.get("Permissions")
    submitted_age = data.get("GetSubmittedAge")
    voice_chat = data.get("VoiceChat")
    custom_name = data.get("CustomNames")
    photon_permission = data.get("PhotonPermission")

    response = {
        "status": "success",
        "UserAge": user_age,
        "Permissions": permissions,
        "GetSubmittedAge": submitted_age,
        "VoiceChat": voice_chat,
        "CustomNames": custom_name,
        "PhotonPermission": photon_permission,
        "AnnouncementData": {
            "ShowAnnouncement": "false",
            "AnnouncementID": "kID_Prelaunch",
            "AnnouncementTitle": "IMPORTANT NEWS",
            "Message": (
                "We're working to make Gorilla Tag a better, more age-appropriate experience "
                "in our next update. To learn more, please check out our Discord."
            )
        }
    }

    return jsonify(response), 200

@app.route("/api/ReturnMyOculusHashV2", methods=["POST"])
def ReturnMyOculusHashV2():
    if request.method != "POST":
        return "", 404

    response = requests.post(
        f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
        headers=settings.get_auth_headers(),
        json={"PlayFabId": request.json["CallerEntityProfile"]["Lineage"]["MasterPlayerAccountId"]}
    )
    
    if response.status_code == 200:
        return jsonify({
            "oculusHash": hashlib.sha256(response.json()["data"]["UserInfo"]["ServerCustomIdInfo"]["CustomId"].replace("OCULUS", "").encode('utf-8')).hexdigest(),
            "error": False
        }), 200
    
    return jsonify({"error": True}), 200

@app.route("/robots.txt", methods=["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"])
def robotstxt():
        return "fuck off bro. thats why ur mom has rainbow hair - louie", 200

@app.route("/api/v3/photon", methods=["POST"])
def photonauth():
    print(f"Received {request.method} request at /api/photon")
    getjson = request.get_json()
    Ticket = getjson.get("Ticket")
    Nonce = getjson.get("Nonce")
    Platform = getjson.get("Platform")
    UserId = getjson.get("UserId")
    nickName = getjson.get("username")
    if request.method.upper() == "GET":
        rjson = request.get_json()
        print(f"{request.method} : {rjson}")

        userId = Ticket.split('-')[0] if Ticket else None
        print(f"Extracted userId: {UserId}")

        if userId is None or len(userId) != 16:
            print("Invalid userId")
            return jsonify({
                'resultCode': 2,
                'message': 'Invalid token',
                'userId': None,
                'nickname': None
            })

        if Platform != 'Quest':
            return jsonify({'Error': 'Bad request', 'Message': 'Invalid platform!'}),403

        if Nonce is None:
            return jsonify({'Error': 'Bad request', 'Message': 'Not Authenticated!'}),304

        req = requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
            json={"PlayFabId": userId},
            headers={
                "content-type": "application/json",
                "X-SecretKey": secretkey
            })

        print(f"Request to PlayFab returned status code: {req.status_code}")

        if req.status_code == 200:
            nickName = req.json().get("UserInfo",
                                      {}).get("UserAccountInfo",
                                              {}).get("Username")
            if not nickName:
                nickName = None

            print(
                f"Authenticated user {userId.lower()} with nickname: {nickName}"
            )

            return jsonify({
                'resultCode': 1,
                'message':
                f'Authenticated user {userId.lower()} title {settings.TitleId.lower()}',
                'userId': f'{userId.upper()}',
                'nickname': nickName
            })
        else:
            print("Failed to get user account info from PlayFab")
            return jsonify({
                'resultCode': 0,
                'message': "Something went wrong",
                'userId': None,
                'nickname': None
            })

    elif request.method.upper() == "POST":
        rjson = request.get_json()
        print(f"{request.method} : {rjson}")

        ticket = rjson.get("Ticket")
        userId = ticket.split('-')[0] if ticket else None
        print(f"Extracted userId: {userId}")

        if userId is None or len(userId) != 16:
            print("Invalid userId")
            return jsonify({
                'resultCode': 2,
                'message': 'Invalid token',
                'userId': None,
                'nickname': None
            })

        req = requests.post(
             url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
             json={"PlayFabId": userId},
             headers={
                 "content-type": "application/json",
                 "X-SecretKey": settings.SecretKey
             })

        print(f"Authenticated user {userId.lower()}")
        print(f"Request to PlayFab returned status code: {req.status_code}")

        if req.status_code == 200:
             nickName = req.json().get("UserInfo",
                                       {}).get("UserAccountInfo",
                                               {}).get("Username")
             if not nickName:
                 nickName = None
             return jsonify({
                 'resultCode': 1,
                 'message':
                 f'Authenticated user {userId.lower()} title {settings.TitleId.lower()}',
                 'userId': f'{userId.upper()}',
                 'nickname': nickName
             })
        else:
             print("Failed to get user account info from PlayFab")
             successJson = {
                 'resultCode': 0,
                 'message': "Something went wrong",
                 'userId': None,
                 'nickname': None
             }
             authPostData = {}
             for key, value in authPostData.items():
                 successJson[key] = value
             print(f"Returning successJson: {successJson}")
             return jsonify(successJson)
    else:
         print(f"Invalid method: {request.method.upper()}")
         return jsonify({
             "Message":
             "Use a POST or GET Method instead of " + request.method.upper()
         })

def ReturnFunctionJson(data, funcname, funcparam={}):
    print(f"Calling function: {funcname} with parameters: {funcparam}")
    rjson = data.get("FunctionParameter", {})
    userId = rjson.get("CallerEntityProfile",
                       {}).get("Lineage", {}).get("TitlePlayerAccountId")

    print(f"UserId: {userId}")

    req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/ExecuteCloudScript",
        json={
            "PlayFabId": userId,
            "FunctionName": funcname,
            "FunctionParameter": funcparam
        },
        headers={
            "content-type": "application/json",
            "X-SecretKey": secretkey
        })

    if req.status_code == 200:
        result = req.json().get("data", {}).get("FunctionResult", {})
        print(f"Function result: {result}")
        return jsonify(result), req.status_code
    else:
        print(f"Function execution failed, status code: {req.status_code}")
        return jsonify({}), req.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9080)
