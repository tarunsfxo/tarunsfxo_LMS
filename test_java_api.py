from app import app
from models import User, CodingProblem, db

with app.app_context():
    user = User.query.first()
    problem = CodingProblem.query.first()
    
    with app.test_client(user=user) as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            
        code = """import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        if (scanner.hasNext()) {
            String inputData = scanner.next();
            System.out.println("hello");
        }
        scanner.close();
    }
}"""
        
        data = {
            "problem_id": problem.id,
            "language": "java",
            "code": code
        }
        res = client.post('/coding/api/submit', json=data)
        print("Status:", res.status_code)
        print("Response:", res.get_data(as_text=True))
