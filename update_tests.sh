#!/bin/bash
find tests/ -type f -name "*.py" -exec sed -i 's/admin_client/super_admin_client/g' {} +
