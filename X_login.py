import base64
import json
import asyncio
from twikit import Client

def decode_and_parse_cookies(base64_cookie):
    try:
        # Decode the Base64 string
        decoded_bytes = base64.b64decode(base64_cookie)
        decoded_str = decoded_bytes.decode('utf-8')

        # Parse the decoded string as JSON
        cookie_list = json.loads(decoded_str)
        cookies = {cookie["name"]: cookie["value"] for cookie in cookie_list if "name" in cookie and "value" in cookie}
        return cookies
    except Exception as e:
        print(f"Error decoding or parsing cookies: {e}")
        return None

def extract_proxy(ip, port, username, password):
    try:
        # Construct proxy string
        return f"http://{username}:{password}@{ip}:{port}"
    except Exception as e:
        print(f"Error constructing proxy: {e}")
        return None

async def main():
    file_path = "cookies/cookies+proxies.txt"  # Update to your file path

    # Read cookies and user-agent data from the file
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    valid_lines = []
    login_successful = False

    for index, line in enumerate(lines, start=1):
        print(f"Try {index}")
        try:
            # Split line into components from the end
            parts = line.strip().split(":")
            if len(parts) < 6:
                print(f"Skipping invalid line: Line {index}")
                continue

            # Extract proxy details
            password = parts[-1]
            username = parts[-2]
            port = parts[-3]
            ip = parts[-4]
            proxy = extract_proxy(ip, port, username, password)

            # Extract user-agent
            user_agent = parts[-5]

            # Extract base64 cookie
            base64_cookie = parts[-6]

            # Decode cookies
            cookies = decode_and_parse_cookies(base64_cookie)
            if not cookies:
                print(f"Skipping line {index} due to invalid cookies.")
                continue

            # Print the proxy being used
            print(f"Using proxy: {proxy}")

            # Set up the client with proxy
            headers = {"User-Agent": user_agent}
            client = Client("en-US", headers=headers, proxy=proxy)
            client.set_cookies(cookies)

            # Attempt login
            try:
                user_info = await client.user()
                print(f"Login successful: {user_info.screen_name}")
                login_successful = True
                break  # Stop at the first successful login
            except Exception as e:
                print(f"Login failed for this cookie: {e}")

        except Exception as e:
            print(f"Error processing line: Line {index} - {e}")

    # Save valid cookies (if any) back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        if login_successful:
            valid_lines.extend(lines[index:])  # Add remaining lines after successful login
            valid_lines.append(line)  # Add only the successful line
        file.writelines(valid_lines)

    print(f"Login was {'successful' if login_successful else 'not successful'}.")
    print(f"Number of valid cookies left: {len(valid_lines)}")

    if login_successful:
        return client  # Return the initialized client
    else:
        print("Login failed. No client initialized.")
    return None

if __name__ == "__main__":
    asyncio.run(main())
