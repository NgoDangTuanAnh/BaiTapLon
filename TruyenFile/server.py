import asyncio
import websockets
import json
import os
import base64
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet # For symmetric encryption (like AES)

# --- Server Configuration ---
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

# --- Storage Paths ---
FILES_DIR = 'files'
KEYS_DIR = 'keys'
DATA_FILE = 'server_data.json' # Renamed to avoid confusion

# Ensure directories exist
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(KEYS_DIR, exist_ok=True)

# --- Data Structures (Server-side) ---
# This will simulate a database for files and their metadata
server_data = {
    "files": [],
    "lecturer_keys": {
        "public": None,
        "private": None
    },
    "classes": [
        {"id": "CT101", "name": "Lập trình cơ bản"},
        {"id": "CT201", "name": "Cấu trúc dữ liệu"},
        {"id": "CT202", "name": "Giải thuật"},
        {"id": "CT301", "name": "Cơ sở dữ liệu"},
        {"id": "CT401", "name": "Mạng máy tính"},
        {"id": "CT501", "name": "Trí tuệ nhân tạo"},
        {"id": "TH101", "name": "Toán cao cấp"},
        {"id": "TH201", "name": "Xác suất thống kê"}
    ],
    "users": { # Placeholder for user management
        "lecturers": {"giangvienA": {"password": "password"}},
        "students": {"sinhvienA": {"password": "password"}}
    }
}

# --- Load/Save Data ---
def load_server_data():
    global server_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Merge loaded data with default to ensure all keys exist
                server_data.update(loaded_data)
                # Ensure classes are loaded correctly without duplication on merge
                if "classes" in loaded_data:
                    server_data["classes"] = loaded_data["classes"]
            print("Server data loaded.")
        except json.JSONDecodeError:
            print("Error loading server_data.json, starting with default data.")
    
    # Load lecturer keys from separate .pem files for robust persistence
    try:
        public_key_path = os.path.join(KEYS_DIR, 'lecturer_public.pem')
        private_key_path = os.path.join(KEYS_DIR, 'lecturer_private.pem')

        if os.path.exists(public_key_path):
            with open(public_key_path, 'rb') as f:
                server_data["lecturer_keys"]["public"] = f.read().decode('utf-8')
        if os.path.exists(private_key_path):
            with open(private_key_path, 'rb') as f:
                server_data["lecturer_keys"]["private"] = f.read().decode('utf-8')
        
        if server_data["lecturer_keys"]["public"] and server_data["lecturer_keys"]["private"]:
            print("Lecturer keys loaded from .pem files.")
        else:
            print("Lecturer keys not found in .pem files or incomplete.")
    except Exception as e:
        print(f"Error loading lecturer keys from files: {e}")

def save_server_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(server_data, f, indent=4, ensure_ascii=False)
    print("Server data saved.")

# --- Cryptography Utilities (Server-side) ---
def generate_rsa_key_pair_server():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return public_pem, private_pem

def sign_data(data_bytes, private_pem_key):
    private_key = serialization.load_pem_private_key(
        private_pem_key.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    signature = private_key.sign(
        data_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(data_bytes, signature_b64, public_pem_key):
    public_key = serialization.load_pem_public_key(
        public_pem_key.encode('utf-8'),
        backend=default_backend()
    )
    try:
        public_key.verify(
    base64.b64decode(signature_b64),
    data_bytes,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False

# Fernet (AES) for symmetric encryption
def generate_fernet_key():
    return Fernet.generate_key().decode('utf-8')

def encrypt_fernet(data_bytes, key_b64):
    f = Fernet(key_b64.encode('utf-8'))
    return base64.b64encode(f.encrypt(data_bytes)).decode('utf-8')

def decrypt_fernet(encrypted_data_b64, key_b64):
    f = Fernet(key_b64.encode('utf-8'))
    return base64.b64encode(f.decrypt(base64.b64decode(encrypted_data_b64))).decode('utf-8')

# --- Request Handlers (Async for WebSocket) ---
async def handle_upload_file_ws(data, websocket):
    file_id = str(datetime.now().timestamp()).replace('.', '')
    file_name = data['fileName']
    file_content_b64 = data['fileContent'] # This is Base64 of the ArrayBuffer
    is_encrypted = data.get('isEncrypted', False)
    is_signed = data.get('isSigned', False)
    course = data.get('course')
    doc_type = data.get('docType')
    description = data.get('description', '')
    uploader = data.get('uploader', 'Unknown')
    original_file_type = data.get('fileType', 'application/octet-stream')

    file_path = os.path.join(FILES_DIR, f"{file_id}_{file_name}")
    
    # Convert Base64 content to bytes
    file_bytes_original = base64.b64decode(data['originalFileContent']) # Original content for signing verification
    file_bytes_processed = base64.b64decode(file_content_b64) # Potentially encrypted bytes

    # Server-side signing (more secure for private key)
    signature = None
    if is_signed:
        if server_data["lecturer_keys"]["private"]:
            # Sign the original file bytes
            signature = sign_data(file_bytes_original, server_data["lecturer_keys"]["private"])
            print(f"File '{file_name}' signed on server.")
        else:
            print("Warning: Lecturer private key not available on server for signing. Relying on client-provided signature.")
            signature = data.get('signature') # Use client's signature if server can't sign

    # Server-side encryption check: For this demo, we assume client encrypts.
    # If the file wasn't encrypted by the client but is_encrypted is true,
    # the server could encrypt it here and generate a new key.
    # For now, we trust client's aesKeyBase64 if is_encrypted is true.
    aes_key_b64 = data.get('aesKeyBase64')

    # Save the processed (potentially encrypted) file content
    with open(file_path, 'wb') as f:
        f.write(file_bytes_processed) # Save the Base64 decoded bytes of the processed content

    new_file_metadata = {
        "id": file_id,
        "name": file_name,
        "size": len(file_bytes_original), # Store original size
        "filePath": file_path, # Server-side path
        "type": original_file_type,
        "course": course,
        "docType": doc_type,
        "description": description,
        "uploadDate": datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
        "uploader": uploader,
        "isEncrypted": is_encrypted,
        "isSigned": is_signed,
        "signature": signature, # Signature from server or client
        "lecturerPublicKey": server_data["lecturer_keys"]["public"], # Server's public key (for verification)
        "aesKeyBase64": aes_key_b64 # Store AES key on server (for demo only, secure storage needed)
    }
    server_data["files"].append(new_file_metadata)
    save_server_data()

    response = {"status": "success", "message": f"File '{file_name}' uploaded successfully!", "action": "upload_file"}
    await send_response_ws(websocket, response)

async def handle_get_files_ws(websocket):
    files_metadata = [
        {
            "id": f["id"],
            "name": f["name"],
            "size": f["size"],
            "type": f["type"],
            "course": f["course"],
            "docType": f["docType"],
            "description": f["description"],
            "uploadDate": f["uploadDate"],
            "uploader": f["uploader"],
            "isEncrypted": f["isEncrypted"],
            "isSigned": f["isSigned"],
            "signature": f["signature"], # Send signature for client verification
            "lecturerPublicKey": f["lecturerPublicKey"] # Send public key for client verification
            # DO NOT SEND 'filePath' or 'aesKeyBase64' directly for security
        } for f in server_data["files"]
    ]
    response = {"status": "success", "files": files_metadata, "action": "get_files"}
    await send_response_ws(websocket, response)

async def handle_download_file_ws(data, websocket):
    file_id = data.get('fileId')
    file_info = next((f for f in server_data["files"] if f["id"] == file_id), None)

    if file_info:
        file_path = file_info["filePath"]
        try:
            with open(file_path, 'rb') as f:
                file_content_bytes_on_server = f.read() # This is the stored (potentially encrypted) content

            file_content_b64 = base64.b64encode(file_content_bytes_on_server).decode('utf-8')

            # Include AES key if it exists and file is encrypted
            # For this demo: send the AES key so client can decrypt.
            # In a real system, the server might decrypt OR securely transmit the AES key
            # encrypted by the student's RSA public key.
            aes_key_b64 = file_info.get('aesKeyBase64') if file_info.get('isEncrypted') else None

            response = {
                "status": "success",
                "action": "download_file",
                "fileName": file_info["name"],
                "fileType": file_info["type"],
                "fileContent": file_content_b64, # Sent content (might be encrypted)
                "isEncrypted": file_info["isEncrypted"],
                "isSigned": file_info["isSigned"],
                "signature": file_info["signature"],
                "lecturerPublicKey": file_info["lecturerPublicKey"],
                "aesKeyBase64": aes_key_b64 # Sending key for client-side decryption demo
            }
            await send_response_ws(websocket, response)
            print(f"Sent file {file_info['name']} (ID: {file_id}) over WebSocket")
        except FileNotFoundError:
            response = {"status": "error", "message": "File not found on server.", "action": "download_file"}
            await send_response_ws(websocket, response)
        except Exception as e:
            response = {"status": "error", "message": f"Error reading file: {str(e)}", "action": "download_file"}
            await send_response_ws(websocket, response)
    else:
        response = {"status": "error", "message": "File not found in metadata.", "action": "download_file"}
        await send_response_ws(websocket, response)

async def handle_get_lecturer_keys_ws(websocket):
    response = {
        "status": "success",
        "action": "get_lecturer_keys",
        "publicKey": server_data["lecturer_keys"]["public"],
        "privateKey": server_data["lecturer_keys"]["private"] # For demo only, NEVER send private key in real app
    }
    await send_response_ws(websocket, response)

async def handle_generate_lecturer_keys_ws(websocket):
    public_key, private_key = generate_rsa_key_pair_server()
    server_data["lecturer_keys"]["public"] = public_key
    server_data["lecturer_keys"]["private"] = private_key # For demo, storing it
    
    # Save keys to files for persistence
    with open(os.path.join(KEYS_DIR, 'lecturer_public.pem'), 'w') as f:
        f.write(public_key)
    with open(os.path.join(KEYS_DIR, 'lecturer_private.pem'), 'w') as f:
        f.write(private_key) # For demo

    save_server_data()
    print("Generated new lecturer keys and saved.")
    response = {
        "status": "success",
        "action": "generate_lecturer_keys",
        "publicKey": public_key,
        "privateKey": private_key # Still sending private key for client-side demo
    }
    await send_response_ws(websocket, response)

async def handle_get_classes_ws(websocket):
    response = {"status": "success", "classes": server_data["classes"], "action": "get_classes"}
    await send_response_ws(websocket, response)

async def handle_add_class_ws(data, websocket):
    class_id = data.get('id')
    class_name = data.get('name')

    if not class_id or not class_name:
        response = {"status": "error", "message": "Class ID and Name are required.", "action": "add_class"}
        await send_response_ws(websocket, response)
        return

    # Check if class already exists
    if any(cls['id'] == class_id for cls in server_data["classes"]):
        response = {"status": "error", "message": f"Class with ID '{class_id}' already exists.", "action": "add_class"}
        await send_response_ws(websocket, response)
        return

    server_data["classes"].append({"id": class_id, "name": class_name})
    save_server_data()
    print(f"Added new class: {class_id} - {class_name}")
    response = {"status": "success", "message": f"Class '{class_name}' added successfully!", "action": "add_class"}
    await send_response_ws(websocket, response)

# --- WebSocket Communication Utilities ---
async def send_response_ws(websocket, response_data):
    try:
        json_response = json.dumps(response_data, ensure_ascii=False)
        await websocket.send(json_response)
    except Exception as e:
        print(f"Error sending WebSocket response: {e}")

# --- WebSocket Client Handling Thread ---
async def websocket_handler(websocket, path):
    print(f"WebSocket client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            try:
                request = json.loads(message)
                action = request.get('action')
                data = request.get('data', {})

                print(f"Received action: {action} from {websocket.remote_address}")

                if action == 'upload_file':
                    await handle_upload_file_ws(data, websocket)
                elif action == 'get_files':
                    await handle_get_files_ws(websocket)
                elif action == 'download_file':
                    await handle_download_file_ws(data, websocket)
                elif action == 'get_lecturer_keys':
                    await handle_get_lecturer_keys_ws(websocket)
                elif action == 'generate_lecturer_keys':
                    await handle_generate_lecturer_keys_ws(websocket)
                elif action == 'get_classes':
                    await handle_get_classes_ws(websocket)
                elif action == 'add_class':
                    await handle_add_class_ws(data, websocket)
                else:
                    await send_response_ws(websocket, {"status": "error", "message": "Invalid action.", "action": action})
            except json.JSONDecodeError:
                await send_response_ws(websocket, {"status": "error", "message": "Invalid JSON format.", "action": "unknown"})
            except Exception as e:
                print(f"Error processing WebSocket request: {e}")
                await send_response_ws(websocket, {"status": "error", "message": f"Server error: {str(e)}", "action": "server_error"})
    except websockets.exceptions.ConnectionClosed:
        print(f"WebSocket client {websocket.remote_address} disconnected.")
    except Exception as e:
        print(f"WebSocket error for {websocket.remote_address}: {e}")

# --- Main Server Loop ---
async def start_websocket_server():
    load_server_data()
    print("Starting WebSocket server...")
    async with websockets.serve(websocket_handler, HOST, PORT):  # Dùng HOST ở trên
        print(f"WebSocket Server listening on ws://{HOST}:{PORT}")
        await asyncio.Future() # Run forever

if __name__ == '__main__':
    asyncio.run(start_websocket_server())