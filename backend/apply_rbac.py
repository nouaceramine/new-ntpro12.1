"""Script to apply RBAC changes to server.py tenant-specific routes"""

with open('/app/backend/server.py', 'r') as f:
    lines = f.readlines()

# Sections that should NOT be changed (line numbers, 1-indexed)
# These are non-tenant routes or dependency definitions
SKIP_SECTIONS = [
    # Dependency definitions
    (454, 472),
    # Auth routes (register, login, unified-login, /auth/me)
    (489, 695),
    # User management (/users CRUD) - needed by both super admin and tenant admin
    (696, 773),
    # SaaS Admin routes (plans, tenants, agents, registration)
    (8189, 9260),
    # Health check
    (9277, 9285),
    # System Updates (Super Admin Only)
    (10024, 10250),
]

def in_skip_section(line_num):
    for start, end in SKIP_SECTIONS:
        if start <= line_num <= end:
            return True
    return False

admin_changes = 0
user_changes = 0

for i in range(len(lines)):
    line_num = i + 1
    line = lines[i]
    
    if in_skip_section(line_num):
        continue
    
    # Don't modify the dependency function definitions themselves
    if 'async def get_admin_user' in line or 'async def get_tenant_admin' in line or \
       'async def require_tenant' in line or 'async def get_super_admin' in line or \
       'async def get_current_user' in line or 'async def get_tenant_user' in line:
        continue
    
    # Replace get_admin_user -> get_tenant_admin for tenant data write ops
    if 'Depends(get_admin_user)' in line:
        lines[i] = line.replace('Depends(get_admin_user)', 'Depends(get_tenant_admin)')
        admin_changes += 1
    
    # Replace get_current_user -> require_tenant for tenant data read ops  
    if 'Depends(get_current_user)' in line:
        lines[i] = line.replace('Depends(get_current_user)', 'Depends(require_tenant)')
        user_changes += 1

with open('/app/backend/server.py', 'w') as f:
    f.writelines(lines)

print(f"Replaced get_admin_user -> get_tenant_admin: {admin_changes} routes")
print(f"Replaced get_current_user -> require_tenant: {user_changes} routes")
print(f"Total changes: {admin_changes + user_changes}")
