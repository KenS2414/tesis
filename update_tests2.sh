#!/bin/bash
find tests/ -type f -name "*.py" -exec sed -i 's/username="admin", password="pass"/username="superadmin", password="superadminpass"/g' {} +
find tests/ -type f -name "*.py" -exec sed -i 's/auth_client/super_admin_client/g' {} +
