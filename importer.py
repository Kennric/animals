import MySQLdb
import simplejson as json
import urllib
import urllib2
import os
import time
import random

# get DB creds from the environment

db_user = os.environ['ANIMALS_DB_USER']
db_pass = os.environ['ANIMALS_DB_PASS']
db_host = os.environ['ANIMALS_DB_HOST']
db_name = os.environ['ANIMALS_DB_NAME']


db = MySQLdb.connect(host=db_host, port=3306, user=db_user, passwd=db_pass,
    db=db_name)

cursor = db.cursor()
# create the tables if they don't exist already

# animals
cursor.execute("CREATE TABLE IF NOT EXISTS animals ( \
                id INT(10) PRIMARY KEY AUTO_INCREMENT, \
                species VARCHAR(255) UNIQUE, \
                common_name VARCHAR(128), \
                image_url VARCHAR(255))")

# questions
cursor.execute("CREATE TABLE IF NOT EXISTS questions ( \
                id INT(10) PRIMARY KEY AUTO_INCREMENT, \
                question VARCHAR(255) UNIQUE)")

# captions
cursor.execute("CREATE TABLE IF NOT EXISTS captions ( \
                id INT(10) PRIMARY KEY AUTO_INCREMENT, \
                caption VARCHAR(255) UNIQUE)")

# results
cursor.execute("CREATE TABLE IF NOT EXISTS results ( \
                id INT(10) PRIMARY KEY AUTO_INCREMENT, \
                caption_id INT(10), \
                animal_id INT(10))")

cursor.close()
db.commit()

# import question list
# store each line in questions table
with open('questions.txt', 'r') as questions:
    cursor = db.cursor()
    for question in questions:
        question = question.strip()
        sql = "INSERT INTO questions (question) \
               VALUES (%s) \
               ON DUPLICATE KEY UPDATE \
               question = %s;"

        print "saving question '%s' to the database" % (question)
        cursor.execute(sql, (question, question))

    cursor.close()
    db.commit()


# import caption list
# store each line in captions table
with open('captions.txt', 'r') as captions:
    cursor = db.cursor()
    for caption in captions:
        caption = caption.strip()
        sql = "INSERT INTO captions (caption) \
               VALUES (%s) \
               ON DUPLICATE KEY UPDATE \
               caption = %s;"

        print "saving caption '%s' to the database" % (caption)
        cursor.execute(sql, (caption, caption))

    cursor.close()
    db.commit()


with open('animals.txt', 'r') as animals:
    for animal in animals:
        cursor = db.cursor()
        common, species = animal.split(';')
        common = " ".join(w.capitalize() for w in common.split())
        common_parts = common.split(',')

        try:
            common_name = "%s %s" % (common_parts[1].strip(), common_parts[0].strip())
        except IndexError:
            common_name = common_parts[0]

        google_url = "https://ajax.googleapis.com/ajax/services/search/images"
        values = {'v': '1.0', 'q': species}
        data = urllib.urlencode(values)

        req = urllib2.Request(google_url + '?' + data)
        try:
            response = urllib2.urlopen(req)
        except HTTPError, e:
            print "google response error"
            print e.reason

        image_json = response.read()
        image_data = json.loads(image_json)

        try:
            image_url = image_data['responseData']['results'][0]['url']
        except:
            print "no image data!"
            continue

        try:
            image = urllib2.urlopen(image_url)
        except:
            print "can't contact image url"

        if image.info()['Content-Type'] != 'image/jpeg':
            print "not an image! " + response.info()['Content-Type']
            continue

        sql = "INSERT INTO animals (species,common_name,image_url) \
               VALUES (\"%s\",\"%s\",\"%s\") \
               ON DUPLICATE KEY UPDATE \
               image_url = \"%s\";" % (species,common_name,image_url,image_url)

        print "saving %s, %s to the database" % (common_name,image_url)
        #print sql

        cursor.execute(sql)
        cursor.close()
        db.commit()
        secs = random.randint(1, 15)
        print "pausing for %s seconds" % secs
        time.sleep(secs)



db.close() 
