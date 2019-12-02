from xhtml2pdf import pisa
from flask import render_template, Flask, Response
from io import BytesIO
from configparser import ConfigParser
import pymysql, sys, hashlib
from datetime import datetime

app=Flask(__name__)
app.debug=False

config = ConfigParser()
config.read('export.conf')
dbExternalConfig = dict(config.items('database'))

try:
    con =  pymysql.connect(**dbExternalConfig)
    cursor = con.cursor(pymysql.cursors.DictCursor)
except Exception as e:
    print(e)
    sys.exit('ОШИБКА: Подключение к главной базе данных не удалось')

@app.route("/export/<int:id>")
def create_pdf(id):
    query = "SELECT id, type, num, date, object_code, name, company, contractor, otdel, comment, status, person FROM contracts WHERE id=%s"
    cursor.execute(query, id)
    result = cursor.fetchone()

    query = "SELECT id, name, created, approved, user FROM signatures WHERE doc= %s ORDER BY id"
    cursor.execute(query, id)
    result['signatures'] = cursor.fetchall()

    if result['status'] == 1 or result['status'] == 3:
        for item in result['signatures']:
            mystring = str(item['created'])+str(item['approved'])
            myhash = hashlib.md5(mystring.encode('utf-8')).hexdigest()
            digitalsig = str(item['id']) + '-' + myhash
            item['digitalsig'] = digitalsig[0:12]
            args = {'user': item['user'], 'doc': id }
            query = "SELECT text FROM notes WHERE author = %(user)s AND doc = %(doc)s"
            cursor.execute(query, args)
            comments = cursor.fetchall()
            item['comments'] = comments

    result['date'] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    filename= "list " + datetime.now().strftime("%d-%m-%Y") + ".pdf"
    template = render_template('hello.html', **result)
    result = BytesIO()
    pdf = pisa.pisaDocument(template, result, encoding='UTF-8')
    if not pdf.err:
        return Response(result.getvalue(), 
        mimetype='application/octet-stream', 
        headers={"Content-Disposition": "attachment;filename=%s" % filename})

if __name__ == "__main__":
    app.run()

