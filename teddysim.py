#! python 3
# coding=UTF-8

import random
import string
import logging
from os.path import expanduser
from flask import Flask, render_template, request, send_from_directory, abort, jsonify
from subprocess import call
from os import listdir
from datetime import datetime
from re import match
from threading import Thread, Lock
from sys import platform


app = Flask(__name__)
local = True

# Logger setup:
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                    datefmt="%d.%m.%Y %H:%M:%S")
logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.CRITICAL)
handler = logging.FileHandler('simlog.log')
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Threading:
th = Thread()
finished = False
finished_thread_name = None
amount_in_queue = 0
lock = Lock()

# This app doesn't need a secret key right now, but it can be added here in the future:
app.secret_key = ""

# Home or Windows user folder:
home = expanduser("~")

if platform.startswith("win"):  # Windows
    path = "\"\"%s\\Desktop\\simc\\simc.exe\"" % home
    # path example: "\"\"C:\\simc\\simc.exe\"" on windows
elif platform.startswith("linux"):  # Linux
    path = "%s/simc/engine/simc" % home
elif platform.startswith("darwin"):  # OS X
    raise SystemExit


realms = ["Darksorrow", "Genjuros", "Neptulon"]
regex_match = "[A-Za-zÆÐƎƏƐƔĲŊŒẞÞǷȜæðǝəɛɣĳŋœĸſßþƿȝĄƁÇĐƊĘĦĮƘŁØƠŞȘŢȚŦŲƯY̨Ƴąɓçđɗęħįƙłøơşșţțŧųưy̨ƴÁÀÂÄǍĂĀÃÅǺĄÆǼǢƁĆĊĈČÇĎḌĐƊÐÉÈĖÊËĚĔĒĘẸƎƏƐĠĜǦĞĢƔáàâäǎăāãåǻąæǽǣɓćċĉčçďḍđɗðéèėêëěĕēęẹǝəɛġĝǧğģɣĤḤĦIÍÌİÎÏǏĬĪĨĮỊĲĴĶƘĹĻŁĽĿʼNŃN̈ŇÑŅŊÓÒÔÖǑŎŌÕŐỌØǾƠŒĥḥħıíìiîïǐĭīĩįịĳĵķƙĸĺļłľŀŉńn̈ňñņŋóòôöǒŏōõőọøǿơœŔŘŖŚŜŠŞȘṢẞŤŢṬŦÞÚÙÛÜǓŬŪŨŰŮŲỤƯẂẀŴẄǷÝỲŶŸȲỸƳŹŻŽẒŕřŗſśŝšşșṣßťţṭŧþúùûüǔŭūũűůųụưẃẁŵẅƿýỳŷÿȳỹƴźżžẓ]{1,12}"
regex_comparison_match = "[A-Za-z0-9/_=,']"

# DEFAULT SETTINGS FOR SIM
# iterations = 10000
# target_error = 0.100
# threads = 2
# calculate_scale_factors = 0


def randomword(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


# Processes input of "name"
def process_input(input1, input2):
    if not match(regex_match, input1) and not match(regex_match, input2):
        return False
    else:
        return True


# Processes input of "trinkets"
def process_input_of_comparison(item):
    if not match(regex_comparison_match, item):
        return False
    else:
        return True


# Simulation function:
def simulate(randomlause, name, realm, scaling, name_compared, itemcompare1, itemcompare2):
    if platform.startswith("win"):
        randomi = " \"html=" + name + "-" + randomlause + ".html\"\""
        execution = ' \"armory=eu,%s,%s\"' % (realm, name)
    elif platform.startswith("linux"):
        randomi = " html=" + name + "-" + randomlause + ".html"
        execution = ' armory=eu,%s,%s' % (realm, name)

    complete = path + execution + randomi
    name_compared = name_compared

    #Threading:
    global finished
    global finished_thread_name
    global amount_in_queue

    try:
        lock.acquire()  # Get lock or wait for lock
        logger.info("New simulation starting for %s, name: %s "
                    % (name, randomlause))
        calculate_scale_factors = 0
        target_error = 0.1
        iterations = 10000
        threads = 4
        complete_compare_string = ''

        if scaling:
            calculate_scale_factors = 1
            target_error = 0.050
            iterations = 10000
            threads = 4

        if itemcompare1 or itemcompare2:
            complete_compare_string = "copy=%s %s %s" % (name_compared, itemcompare1, itemcompare2)

        # This call method runs only on Windows
        if platform.startswith("win"):
            call("cmd /C %s hosted_html=1 iterations=%s target_error=%s threads=%s calculate_scale_factors=%s %s" %
                (complete, iterations, target_error, threads, calculate_scale_factors, complete_compare_string),
                 shell=True)

        # test if this runs on linux:
        elif platform.startswith("linux"):
            call("%s hosted_html=1 iterations=%s target_error=%s threads=%s calculate_scale_factors=%s %s" %
                (complete, iterations, target_error, threads, calculate_scale_factors, complete_compare_string),
                shell=True)

    except Exception as e:
        logger.info("Exception: ", name, e)
        return render_template('frontcontent.html',
                               error="Error with simulation", realms=realms)

    finally:
        lock.release()  # Always release the lock no matter what

    # API's use these variables:
    finished_thread_name = randomlause
    finished = True
    amount_in_queue -= 1


@app.route("/", methods=['GET', 'POST'])
def form():
    timenow = datetime.now().strftime('%d.%m.%Y - %H:%M')
    return render_template('frontcontent.html',
                           timenow=timenow, realms=realms)


@app.route("/list")
def lista():
    timenow = datetime.now().strftime('%d.%m.%Y - %H:%M    ')
    list_of_html = [s for s in listdir() if s.endswith('.html')]
    return render_template('listcontent.html',
                           list=list_of_html, timenow=timenow)


@app.route("/result", methods=['GET', 'POST'])
def handle():
    if request.method == 'POST':
        name = request.form['charactername']
        realm = request.form['realm']
        scaling = request.form.get('scale')
        name_compared = ""
        itemcompare1 = ""
        itemcompare2 = ""

        # Threading :
        global th
        global finished
        global amount_in_queue
        finished = False

        # Get user inputs:
        if request.form['compare1']:
            itemcompare1 = request.form['compare1']
        if request.form['compare2']:
            itemcompare2 = request.form['compare2']
        if request.form['compare1'] or request.form['compare2']:
            name_compared = name + "_COMPARED"

        # Check user input against regex server side
        if itemcompare1 and not \
            process_input_of_comparison(itemcompare1) or \
            itemcompare2 and not \
            process_input_of_comparison(itemcompare2):

            logger.warning("%s had error with item compare regex: %s %s" %
                           (request.remote_addr, itemcompare1, itemcompare2))

            return render_template('frontcontent.html',
                                   error="Item compare error.",
                                   realms=realms)

        if not process_input(name, realm):
            logger.warning("%s had error with name input regex: %s" %
                           (request.remote_addr, name))

            return render_template('frontcontent.html',
                                   error="Error with input.",
                                   realms=realms)
        else:
            # Everything went OK and we let the user to create a thread for simming
            randomlause = randomword(15)
            th = Thread(target=simulate, args=(randomlause, name,
                                               realm, scaling,
                                               name_compared,
                                               itemcompare1, itemcompare2))
            th.name = randomlause
            logger.info("%s - - %s" % (request.remote_addr, name))
            th.start()
            amount_in_queue += 1
            return render_template('form_action.html', name=name, randomlause=randomlause,
                                   amount_in_queue=amount_in_queue)

    else:
        # Returning this usually means user tried to access /result directly
        return render_template('frontcontent.html',
                               error="No results (yet)!",
                               realms=realms)


@app.route("/<htmldoc>.html")
def documents(htmldoc):
    # Allows access to any static html file on server, if they exist
    try:
        return send_from_directory('', "%s.html" % htmldoc)
    except Exception:
        return abort(404)


@app.route("/robots.txt")
def robots():
    return send_from_directory('', "robots.txt")


# API for last finished thread status:
@app.route('/status')
def thread_status():
    return jsonify(dict(status=(finished_thread_name if finished else 'running')))


# API for queue total status:
@app.route('/queue_status')
def queue_status():
    global amount_in_queue
    return jsonify(dict(status=amount_in_queue))


# Basic error handlers:
@app.errorhandler(404)
def page_not_found(e):
    return render_template('frontcontent.html',
                           title="Teddy simmer - 404 Error",
                           error="Error happened! (404 not found)",
                           realms=realms), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('frontcontent.html',
                           title="Teddy simmer - 500 Error",
                           error="Error happened! (500 internal error)",
                           realms=realms), 500

if __name__ == "__main__":
    if local:
        logger.info("Starting the app locally")
        app.run(threaded=True)
    else:
        logger.info("Starting the app publicly")
        app.run(host='0.0.0.0', port=80)
