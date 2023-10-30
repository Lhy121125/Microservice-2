from flask import Flask


app = Flask(__name__)


@app.route('/')
def root():  # put application's code here
    return """This is the google app engine feature.<br> 
    We will use this to deploy cover letter service:)<br>
    To be continued..."""

@app.route('/students', methods=['GET'])
def getStudents():
    students = f"""
    Here are the list of students:<br>
    dz2506,<br>
    qw2324,<br>
    hl3648,<br>
    ly2555,<br>
    cs4206
    """
    return students

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080,debug=True)
