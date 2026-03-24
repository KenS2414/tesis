sed -i 's/role="admin"/role="super_admin"/g' tests/test_crud.py tests/test_crud_subjects_grades.py tests/test_permissions_edit_delete.py
sed -i "s/role='admin'/role='super_admin'/g" tests/test_crud.py tests/test_crud_subjects_grades.py tests/test_permissions_edit_delete.py
