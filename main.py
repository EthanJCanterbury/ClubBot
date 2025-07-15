
import os
import json
import requests
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/invite-to-channel', methods=['POST'])
def invite_to_channel():
    """
    Invite a user by email to a specific Slack channel using undocumented users.admin.inviteBulk
    Expected JSON payload:
    {
        "email": "user@example.com",
        "channel_id": "C1234567890"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        email = data.get('email')
        channel_id = data.get('channel_id')
        
        # Get tokens from environment variables
        xoxc_token = os.getenv('SLACK_XOXC')
        xoxd_token = os.getenv('SLACK_XOXD')
        team_id = os.getenv('SLACK_TEAM_ID', 'T0266FRGM')  # Default to hackclub team
        
        if not all([email, channel_id]):
            return jsonify({"error": "Missing required fields: email, channel_id"}), 400
            
        if not all([xoxc_token, xoxd_token]):
            return jsonify({"error": "Slack tokens not configured in environment"}), 500
        
        # Invite using undocumented bulk invite endpoint
        success, error_details = invite_user_bulk(email, channel_id, xoxc_token, xoxd_token, team_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Successfully invited {email} to channel {channel_id}"
            }), 200
        else:
            return jsonify({"error": "Failed to invite user", "details": error_details}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def invite_user_bulk(email, channel_id, xoxc_token, xoxd_token, team_id):
    """Invite user using undocumented users.admin.inviteBulk endpoint"""
    try:
        # Generate unique IDs for the request (similar to what Slack web client does)
        timestamp = str(int(time.time() * 1000))
        x_id = f"invite-{timestamp}"
        
        # Build the URL with query parameters like the real request
        url = "https://slack.com/api/users.admin.inviteBulk"
        params = {
            "_x_id": x_id,
            "_x_csid": "replit-bot",
            "slack_route": team_id,
            "_x_version_ts": timestamp,
            "_x_frontend_build_type": "current",
            "_x_desktop_ia": "4",
            "_x_gantry": "true",
            "fp": "71",
            "_x_num_retries": "0"
        }
        
        # Set up headers to mimic the real browser request
        headers = {
            "Cookie": f"d={xoxd_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Origin": "https://app.slack.com",
            "Referer": "https://app.slack.com/",
            "Authority": "slack.com"
        }
        
        # Prepare form data using multipart/form-data format
        form_data = {
            "token": (None, xoxc_token),
            "invites": (None, json.dumps([{
                "email": email,
                "type": "ultra_restricted",  # Guest user type
                "mode": "manual"
            }])),
            "team_id": (None, team_id),
            "restricted": (None, "false"),
            "ultra_restricted": (None, "true"),
            "campaign": (None, "channel_sidebar"),
            "channels": (None, channel_id),
            "_x_reason": (None, "submit-invite-to-workspace-invites"),
            "_x_mode": (None, "online"),
            "_x_sonic": (None, "true"),
            "_x_app_name": (None, "clientinvites")
        }
        
        response = requests.post(url, params=params, headers=headers, files=form_data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("ok"):
                    return True, None
                else:
                    error_msg = f"Slack API error: {data.get('error', 'unknown')} - {data}"
                    return False, error_msg
            except json.JSONDecodeError:
                # Sometimes the response might not be JSON
                return False, f"Non-JSON response: {response.text}"
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            return False, error_msg
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"Error in bulk invite: {e}")
        return False, error_msg

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
