from app import create_app
from blueprints.coding import execute_local

app = create_app()

with app.app_context():
    code_c = """
#include <stdio.h>
int main() {
    printf("Hello from C!");
    return 0;
}
    """
    res = execute_local("c", code_c, "", 5)
    print("C Result:", res)
