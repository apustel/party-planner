import boto3
import json
import os
import urllib3

s3 = boto3.client('s3')
http = urllib3.PoolManager()

def send_response(event, context, response_status, response_data):
    response_body = {
        'Status': response_status,
        'Reason': f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
        'PhysicalResourceId': context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data
    }

    response_url = event['ResponseURL']

    # Sende die Antwort an die CloudFormation ResponseURL
    encoded_response = json.dumps(response_body).encode('utf-8')
    headers = {'content-type': '', 'content-length': str(len(encoded_response))}
    try:
        response = http.request('PUT', response_url, body=encoded_response, headers=headers)
        print(f"Status code: {response.status}")
    except Exception as e:
        print(f"Error sending response to CloudFormation: {e}")

def lambda_handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']
    registration_api = os.environ['REGISTRATION_API']
    file_content = f"""<!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Party Planner Formular</title>
    </head>
    <body>
        <h2>Party Planner</h2>
        <form id="putForm" onsubmit="sendPostRequest(event)">
            <label for="feld1">PartyName:</label>
            <input type="text" id="feld1" name="feld1" required><br><br>
            
            <label for="feld2">PartyDate:</label>
            <input type="text" id="feld2" name="feld2" required><br><br>
            
            <label for="feld3">GuestName:</label>
            <input type="text" id="feld3" name="feld3" required><br><br>
            
            <label for="feld4">GuestDiet:</label>
            <input type="text" id="feld4" name="feld4" required><br><br>
            
            <button type="submit">Absenden</button>
        </form>

        <script>
            async function sendPostRequest(event) {{
                event.preventDefault();
                
                // URL des AWS API Gateway Endpoints
                const url = "https://{registration_api}.execute-api.eu-central-1.amazonaws.com/Prod/register/";
                
                // Formulardaten sammeln und als JSON formatieren
                const data = {{
                    PartyName: document.getElementById("feld1").value,
                    PartyDate: document.getElementById("feld2").value,
                    GuestName: document.getElementById("feld3").value,
                    GuestDiet: document.getElementById("feld4").value,
                }};
                
                try {{
                    const response = await fetch(url, {{
                        method: "POST",  // Methode auf POST ändern
                        headers: {{
                            "Content-Type": "application/json",
                        }},
                        body: JSON.stringify(data)  // Daten als JSON
                    }});
                    
                    if (response.ok) {{
                        alert("Daten erfolgreich gesendet!");
                        document.getElementById("putForm").reset(); // Formular zurücksetzen
                    }} else {{
                        alert(`Fehler beim Senden der Daten.`);
                    }}
                }} catch (error) {{
                    alert("Es ist ein Fehler aufgetreten: " + error.message);
                }}
            }}
        </script>
    </body>
    </html>"""

    try:
        s3.put_object(
            Bucket=bucket_name,
            Key='index.html',
            Body=file_content,
            ContentType='text/html'
        )
        send_response(event, context, "SUCCESS", {"Message": "File uploaded successfully"})

    except Exception as e:
            print(f"Error uploading file: {e}")
            # Fehler an CloudFormation zurückmelden
            send_response(event, context, "FAILED", {"Message": str(e)})
            
    return {
        'statusCode': 200,
        'body': json.dumps('File uploaded')
    }