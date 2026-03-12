from werkzeug.security import generate_password_hash

# Instructions: Add New User to Your Patient Management System
# 
# 1. Run this script to generate a password hash
# 2. Add the username and hash to your Google Sheet "Users" tab
#
# The Users sheet should have these columns:
# | username | password_hash | role |

print("=" * 60)
print("PASSWORD HASH GENERATOR")
print("=" * 60)
print()

# Get username and password from user
username = input("Enter new username: ")
password = input("Enter new password: ")
role = input("Enter role (admin/doctor/staff): ") or "doctor"

# Generate password hash
password_hash = generate_password_hash(password)

print()
print("=" * 60)
print("ADD THIS ROW TO YOUR GOOGLE SHEET 'Users' TAB:")
print("=" * 60)
print()
print(f"Username:      {username}")
print(f"Password Hash: {password_hash}")
print(f"Role:          {role}")
print()
print("=" * 60)
print("INSTRUCTIONS:")
print("=" * 60)
print("1. Open your Google Sheet: 'Hospital Patient Data'")
print("2. Go to the 'Users' tab")
print("3. Add a new row with these three values:")
print(f"   - Column A (username): {username}")
print(f"   - Column B (password_hash): {password_hash}")
print(f"   - Column C (role): {role}")
print("4. Save the sheet")
print("5. You can now login with:")
print(f"   Username: {username}")
print(f"   Password: {password}")
print("=" * 60)
