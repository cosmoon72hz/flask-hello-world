import json
import random
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

TitleId = "DF2F4"
SecretKey = "UCAKYJEFJJ4GHS74ZK8FC14CFSTQG5TBXBFXBCJH5KUBBDR3A4"
ApiKey = "OC|9835875326522978|dba3cebc394f5dc975e184362896135d"
DiscordWebhook = "https://discord.com/api/webhooks/1285066506375401534/SM2e9BYT3FWIkHqXz9hEanJRjKZDlbm8aGlvKYoRmgIItiu58Fry_YOfGqctTnjlKaHB"
def GetAuthHeaders() -> dict:
    return {"Content-Type": "application/json", "X-SecretKey": SecretKey}

@app.route("/api/PlayFabAuthentication", methods=["POST"])
def playfab_authentication():
    rjson = request.get_json()
    required_fields = ["CustomId", "Nonce", "AppId", "Platform", "OculusId"]
    missing_fields = [field for field in required_fields if not rjson.get(field)]

    if missing_fields:
        return (
            jsonify(
                {
                    "Message": f"Missing parameter(s): {', '.join(missing_fields)}",
                    "Error": f"BadRequest-No{missing_fields[0]}",
                }
            ),
            400,
        )

    if rjson.get("AppId") != TitleId:
        return (
            jsonify(
                {
                    "Message": "Request sent for the wrong App ID",
                    "Error": "BadRequest-AppIdMismatch",
                }
            ),
            400,
        )

    if not rjson.get("CustomId").startswith(("OC", "PI")):
        return (
            jsonify({"Message": "Bad request", "Error": "BadRequest-IncorrectPrefix"}),
            400,
        )
        
    discord_message(rjson)
    
    url = f"https://{TitleId}.playfabapi.com/Server/LoginWithServerCustomId"
    login_request = requests.post(
        url=url,
        json={
            "ServerCustomId": rjson.get("CustomId"),
            "CreateAccount": True
        },
        headers=GetAuthHeaders()
    )

    if login_request.status_code == 200:
        data = login_request.json().get("data")
        session_ticket = data.get("SessionTicket")
        entity_token = data.get("EntityToken").get("EntityToken")
        playfab_id = data.get("PlayFabId")
        entity_type = data.get("EntityToken").get("Entity").get("Type")
        entity_id = data.get("EntityToken").get("Entity").get("Id")

        link_response = requests.post(
            url=f"https://{TitleId}.playfabapi.com/Server/LinkServerCustomId",
            json={
                "ForceLink": True,
                "PlayFabId": playfab_id,
                "ServerCustomId": rjson.get("CustomId"),
            },
            headers=GetAuthHeaders()
        ).json()

        return (
            jsonify(
                {
                    "PlayFabId": playfab_id,
                    "SessionTicket": session_ticket,
                    "EntityToken": entity_token,
                    "EntityId": entity_id,
                    "EntityType": entity_type,
                }
            ),
            200,
        )
    else:
        if login_request.status_code == 403:
            ban_info = login_request.json()
            if ban_info.get("errorCode") == 1002:
                ban_message = ban_info.get("errorMessage", "No ban message provided.")
                ban_details = ban_info.get("errorDetails", {})
                ban_expiration_key = next(iter(ban_details.keys()), None)
                ban_expiration_list = ban_details.get(ban_expiration_key, [])
                ban_expiration = (
                    ban_expiration_list[0]
                    if len(ban_expiration_list) > 0
                    else "No expiration date provided."
                )
                print(ban_info)
                return (
                    jsonify(
                        {
                            "BanMessage": ban_expiration_key,
                            "BanExpirationTime": ban_expiration,
                        }
                    ),
                    403,
                )
            else:
                error_message = ban_info.get(
                    "errorMessage", "Forbidden without ban information."
                )
                return (
                    jsonify({"Error": "PlayFab Error", "Message": error_message}),
                    403,
                )
        else:
            error_info = login_request.json()
            error_message = error_info.get("errorMessage", "An error occurred.")
            return (
                jsonify({"Error": "PlayFab Error", "Message": error_message}),
                login_request.status_code,
            )     

@app.route("/api/CachePlayFabId", methods=["POST"])
def cacheplayfabid():
    idfk = request.get_json()
    playfabid = idfk.get("SessionTicket").split("-")[0] if "SessionTicket" in idfk else None
    if playfabid is None:
        return jsonify({"Message": "Try Again Later."}), 404
    return jsonify({"Message": "Authed", "PlayFabId": playfabid}), 200

@app.route("/", methods=["POST", "GET"])
def Rizz():
    return "cosmo has made this backend!"

@app.route("/api/TitleData", methods=["POST", "GET"])
def title_data():
    response = requests.post(
        url=f"https://{TitleId}.playfabapi.com/Server/GetTitleData",
        headers=GetAuthHeaders()
    )

    if response.status_code == 200:
        return jsonify(response.json().get("data").get("Data"))
    else:
        return jsonify({}), response.status_code

@app.route("/api/CheckForBadName", methods=["POST"])
def check_for_bad_name():
    rjson = request.get_json().get("FunctionResult")
    name = rjson.get("name").upper()

    if name in ["KKK", "PENIS", "NIGG", "NEG", "NIGA", "MONKEYSLAVE", "SLAVE", "FAG", 
        "NAGGI", "TRANNY", "QUEER", "KYS", "DICK", "PUSSY", "VAGINA", "BIGBLACKCOCK", 
        "DILDO", "HITLER", "KKX", "XKK", "NIGA", "NIGE", "NIG", "NI6", "PORN", 
        "JEW", "JAXX", "TTTPIG", "SEX", "COCK", "CUM", "FUCK", "PENIS", "DICK", 
        "ELLIOT", "JMAN", "K9", "NIGGA", "TTTPIG", "NICKER", "NICKA", 
        "REEL", "NII", "@here", "!", " ", "JMAN", "PPPTIG", "CLEANINGBOT", "JANITOR", "K9", 
        "H4PKY", "MOSA", "NIGGER", "NIGGA", "IHATENIGGERS", "@everyone", "TTT", "FATE"]:
        return jsonify({"result": 2})
    else:
        return jsonify({"result": 0})

@app.route("/api/ConsumeOculusIAP", methods=["POST"])
def consume_oculus_iap():
    rjson = request.get_json()
    access_token = rjson.get("userToken")
    user_id = rjson.get("userID")
    nonce = rjson.get("nonce")
    sku = rjson.get("sku")

    response = requests.post(
        url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={user_id}&sku={sku}&access_token={ApiKey}",
        headers={"content-type": "application/json"}
    )

    if response.json().get("success"):
        return jsonify({"result": True})
    else:
        return jsonify({"error": True})

@app.route('/api/BroadcastMyRoom', methods=['POST', 'GET'])
def Broad():
    returndata = request.get_json()
    return ReturnFunctionJson(returndata, "BroadcastMyRoom", returndata.get("FunctionParameter"))

@app.route('/api/ReturnOculusHash', methods=['POST', 'GET'])
def Hash():
    return_data = request.get_json()
    return ReturnFunctionJson(return_data, "ReturnMyOculusHash")

@app.route('/api/TryDistributeCurrency', methods=['POST', 'GET'])
def currency():
    return_data = request.get_json()
    print(json.dumps(return_data, indent=2))
    return jsonify({
        "Message": "Moneys"
    }), 200

@app.route('/api/AddOrRemoveDLCOwnership', methods=['POST', 'GET'])
def AddOrRemoveDLCOwnership():
    data = request.json
    PlayFabId = data['CallerEntityProfile']['Lineage']['MasterPlayerAccountId']
    return jsonify(True)

@app.route('/api/GetRandomName', methods=['POST', 'GET'])
def GetName():
    return jsonify({"result": f"GORILLA{random.randint(1000,9999)}"})

@app.route("/api/photon", methods=["POST"])
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
            url=f"https://{TitleId}.playfabapi.com/Server/GetUserAccountInfo",
            json={"PlayFabId": userId},
            headers={
                "content-type": "application/json",
                "X-SecretKey": SecretKey
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
                f'Authenticated user {userId.lower()} title {TitleId.lower()}',
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
             url=f"https://{TitleId}.playfabapi.com/Server/GetUserAccountInfo",
             json={"PlayFabId": userId},
             headers={
                 "content-type": "application/json",
                 "X-SecretKey": SecretKey
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
                 f'Authenticated user {userId.lower()} title {TitleId.lower()}',
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
def discord_message(message):
  payload = {"content": message}
  headers = {'Content-Type': 'application/json'}
  requests.post(
      f"{DiscordWebhook}", 
      json=payload, 
      headers=headers
    )

def ReturnFunctionJson(data, funcname, funcparam={}):
    print(f"Calling function: {funcname} with parameters: {funcparam}")
    rjson = data.get("FunctionParameter", {})
    userId = rjson.get("CallerEntityProfile",
                       {}).get("Lineage", {}).get("TitlePlayerAccountId")

    print(f"UserId: {userId}")

    req = requests.post(
        url=f"https://{TitleId}.playfabapi.com/Server/ExecuteCloudScript",
        json={
            "PlayFabId": userId,
            "FunctionName": funcname,
            "FunctionParameter": funcparam
        },
        headers={
            "content-type": "application/json",
            "X-SecretKey": SecretKey
        })

    if req.status_code == 200:
        result = req.json().get("data", {}).get("FunctionResult", {})
        print(f"Function result: {result}")
        return jsonify(result), req.status_code
    else:
        print(f"Function execution failed, status code: {req.status_code}")
        return jsonify({}), req.status_code

if __name__ == "__main__":
    app.run(debug=True)
    QuestThing = {"AllActiveQuests": {
		"DailyQuests": [
			{
				"selectCount": 1,
				"name": "Gameplay",
				"quests": [
					{
						"disable": false,
						"questID": 11,
						"weight": 1,
						"questName": "PLAY INFECTION",
						"questType": "gameModeRound",
						"questOccurenceFilter": "INFECTION",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"forest",
							"canyon",
							"beach",
							"mountain",
							"skyJungle",
							"cave",
							"Metropolis",
							"bayou",
							"rotating",
							"none"
						]
					},
					{
						"disable": true,
						"questID": 19,
						"weight": 1,
						"questName": "PLAY PAINTBRAWL",
						"questType": "gameModeRound",
						"questOccurenceFilter": "PAINTBRAWL",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"forest",
							"canyon",
							"beach",
							"mountain",
							"skyJungle",
							"cave",
							"Metropolis",
							"bayou",
							"rotating",
							"none"
						]
					},
					{
						"disable": false,
						"questID": 13,
						"weight": 1,
						"questName": "PLAY FREEZE TAG",
						"questType": "gameModeRound",
						"questOccurenceFilter": "FREEZE TAG",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"forest",
							"canyon",
							"beach",
							"mountain",
							"skyJungle",
							"cave",
							"Metropolis",
							"bayou",
							"rotating",
							"none"
						]
					},
					{
						"disable": false,
						"questID": 1,
						"weight": 1,
						"questName": "PLAY GUARDIAN",
						"questType": "gameModeRound",
						"questOccurenceFilter": "GUARDIAN",
						"requiredOccurenceCount": 5,
						"requiredZones": [
							"forest",
							"canyon",
							"beach",
							"mountain",
							"cave",
							"Metropolis",
							"bayou",
							"none"
						]
					},
					{
						"disable": false,
						"questID": 4,
						"weight": 1,
						"questName": "TAG PLAYERS",
						"questType": "misc",
						"questOccurenceFilter": "GameModeTag",
						"requiredOccurenceCount": 2,
						"requiredZones": [
							"none"
						]
					}
				]
			},
			{
				"selectCount": 3,
				"name": "Exploration",
				"quests": [
					{
						"disable": false,
						"questID": 5,
						"weight": 1,
						"questName": "RIDE THE SHARK",
						"questType": "grabObject",
						"questOccurenceFilter": "ReefSharkRing",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 9,
						"weight": 1,
						"questName": "PLAY THE PIANO",
						"questType": "tapObject",
						"questOccurenceFilter": "Piano_Collapsed_Key",
						"requiredOccurenceCount": 10,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 14,
						"weight": 1,
						"questName": "THROW SNOWBALLS",
						"questType": "launchedProjectile",
						"questOccurenceFilter": "SnowballProjectile",
						"requiredOccurenceCount": 10,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 15,
						"weight": 1,
						"questName": "GO FOR A SWIM",
						"questType": "swimDistance",
						"questOccurenceFilter": "",
						"requiredOccurenceCount": 200,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 21,
						"weight": 1,
						"questName": "CLIMB THE TALLEST TREE",
						"questType": "enterLocation",
						"questOccurenceFilter": "TallestTree",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"forest"
						]
					},
					{
						"disable": false,
						"questID": 22,
						"weight": 1,
						"questName": "COMPLETE THE OBSTACLE COURSE",
						"questType": "enterLocation",
						"questOccurenceFilter": "ObstacleCourse",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 23,
						"weight": 1,
						"questName": "SWIM UNDER A WATERFALL",
						"questType": "enterLocation",
						"questOccurenceFilter": "UnderWaterfall",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 24,
						"weight": 1,
						"questName": "SNEAK UPSTAIRS IN THE STORE",
						"questType": "enterLocation",
						"questOccurenceFilter": "SecretStore",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 25,
						"weight": 1,
						"questName": "CLIMB INTO THE CROW'S NEST",
						"questType": "enterLocation",
						"questOccurenceFilter": "CrowsNest",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 26,
						"weight": 1,
						"questName": "GO FOR A WALK",
						"questType": "moveDistance",
						"questOccurenceFilter": "",
						"requiredOccurenceCount": 500,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 28,
						"weight": 1,
						"questName": "GET SMALL",
						"questType": "misc",
						"questOccurenceFilter": "SizeSmall",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 29,
						"weight": 1,
						"questName": "GET BIG",
						"questType": "misc",
						"questOccurenceFilter": "SizeLarge",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 31,
						"weight": 1,
						"questName": "ADD A CRITTER TO YOUR COLLECTION",
						"questType": "critter",
						"questOccurenceFilter": "Collect",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 32,
						"weight": 1,
						"questName": "DONATE A CRITTER",
						"questType": "critter",
						"questOccurenceFilter": "Donate",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					}
				]
			},
			{
				"selectCount": 1,
				"name": "Social",
				"quests": [
					{
						"disable": false,
						"questID": 2,
						"weight": 1,
						"questName": "HIGH FIVE PLAYERS",
						"questType": "triggerHandEffect",
						"questOccurenceFilter": "HIGH_FIVE",
						"requiredOccurenceCount": 10,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 3,
						"weight": 1,
						"questName": "FIST BUMP PLAYERS",
						"questType": "triggerHandEffect",
						"questOccurenceFilter": "FIST_BUMP",
						"requiredOccurenceCount": 10,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 16,
						"weight": 1,
						"questName": "FIND SOMETHING TO EAT",
						"questType": "eatObject",
						"questOccurenceFilter": "",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 30,
						"weight": 1,
						"questName": "MAKE A FRIENDSHIP BRACELET",
						"questType": "misc",
						"questOccurenceFilter": "FriendshipGroupJoined",
						"requiredOccurenceCount": 1,
						"requiredZones": [
							"none"
						]
					}
				]
			}
		],
		"WeeklyQuests": [
			{
				"selectCount": 1,
				"name": "Gameplay",
				"quests": [
					{
						"disable": false,
						"questID": 17,
						"weight": 1,
						"questName": "PLAY INFECTION",
						"questType": "gameModeRound",
						"questOccurenceFilter": "INFECTION",
						"requiredOccurenceCount": 5,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": true,
						"questID": 20,
						"weight": 1,
						"questName": "PLAY PAINTBRAWL",
						"questType": "gameModeRound",
						"questOccurenceFilter": "PAINTBRAWL",
						"requiredOccurenceCount": 5,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 8,
						"weight": 1,
						"questName": "PLAY FREEZE TAG",
						"questType": "gameModeRound",
						"questOccurenceFilter": "FREEZE TAG",
						"requiredOccurenceCount": 5,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 10,
						"weight": 1,
						"questName": "PLAY GUARDIAN",
						"questType": "gameModeRound",
						"questOccurenceFilter": "GUARDIAN",
						"requiredOccurenceCount": 25,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 12,
						"weight": 1,
						"questName": "TAG PLAYERS",
						"questType": "misc",
						"questOccurenceFilter": "GameModeTag",
						"requiredOccurenceCount": 10,
						"requiredZones": [
							"none"
						]
					}
				]
			},
			{
				"selectCount": 1,
				"name": "Exploration and Social",
				"quests": [
					{
						"disable": false,
						"questID": 33,
						"weight": 1,
						"questName": "COLLECT CRITTERS",
						"questType": "critter",
						"questOccurenceFilter": "Collect",
						"requiredOccurenceCount": 5,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 34,
						"weight": 1,
						"questName": "DONATE CRITTERS",
						"questType": "critter",
						"questOccurenceFilter": "Donate",
						"requiredOccurenceCount": 10,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 6,
						"weight": 1,
						"questName": "THROW SNOWBALLS",
						"questType": "launchedProjectile",
						"questOccurenceFilter": "SnowballProjectile",
						"requiredOccurenceCount": 50,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 7,
						"weight": 1,
						"questName": "GO FOR A LONG SWIM",
						"questType": "swimDistance",
						"questOccurenceFilter": "",
						"requiredOccurenceCount": 1000,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 18,
						"weight": 1,
						"questName": "EAT FOOD",
						"questType": "eatObject",
						"questOccurenceFilter": "",
						"requiredOccurenceCount": 25,
						"requiredZones": [
							"none"
						]
					},
					{
						"disable": false,
						"questID": 27,
						"weight": 1,
						"questName": "GO FOR A LONG WALK",
						"questType": "moveDistance",
						"questOccurenceFilter": "",
						"requiredOccurenceCount": 2500,
						"requiredZones": [
							"none"
						]
					}
				]
			}
		]
	}
}



@app.route("/api/GetDailyQuests", methods=["GET", "POST", "PUT"])
def skid():
    return jsonify(QuestThing), 200
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
	@app.route("/GetFriends", methods=["POST", "GET"])
def get_friends():
    data = request.get_json()
    pID = data.get("PlayFabId")
    url = f"https://{settings.TitleId}.playfabapi.com/Server/GetFriendsList"
    headers = {
        "X-SecretKey": Settings.SecretKey,
        "Content-Type": "application/json"
    }
    payload = {
        "PlayFabId": pID,
    }
    res = requests.post(url, headers=headers, json=payload)
    return jsonify(res.json()), res.status_code will not work prob but just something to showcase
