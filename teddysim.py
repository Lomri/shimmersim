#! python 3
# coding=UTF-8

import random
import string
from os.path import expanduser
from flask import Flask, render_template, request, send_from_directory, abort, jsonify
from subprocess import call
from os import listdir
from datetime import datetime
from re import match
from threading import Thread, Lock
import logging


app = Flask(__name__)

# Logger setup:
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                    datefmt="%d.%m.%Y %H:%M:%S")
logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.CRITICAL)


# Threading:
th = Thread()
finished = False
finished_thread_name = None
amount_in_queue = 0
lock = Lock()

local = True

# This app doesn't need a secret key right now, but it can be added here in the future:
app.secret_key = ""

# this should work cross-platform for the home folder (Windows user folder):
home = expanduser("~")
path = "\"\"%s\\Desktop\\simc\\simc.exe\"" % home
# path example: "\"\"C:\\simc\\simc.exe\""

realms = ["Darksorrow", "Genjuros", "Neptulon"]
regex_match = "[A-Za-zÆÐƎƏƐƔĲŊŒẞÞǷȜæðǝəɛɣĳŋœĸſßþƿȝĄƁÇĐƊĘĦĮƘŁØƠŞȘŢȚŦŲƯY̨Ƴąɓçđɗęħįƙłøơşșţțŧųưy̨ƴÁÀÂÄǍĂĀÃÅǺĄÆǼǢƁĆĊĈČÇĎḌĐƊÐÉÈĖÊËĚĔĒĘẸƎƏƐĠĜǦĞĢƔáàâäǎăāãåǻąæǽǣɓćċĉčçďḍđɗðéèėêëěĕēęẹǝəɛġĝǧğģɣĤḤĦIÍÌİÎÏǏĬĪĨĮỊĲĴĶƘĹĻŁĽĿʼNŃN̈ŇÑŅŊÓÒÔÖǑŎŌÕŐỌØǾƠŒĥḥħıíìiîïǐĭīĩįịĳĵķƙĸĺļłľŀŉńn̈ňñņŋóòôöǒŏōõőọøǿơœŔŘŖŚŜŠŞȘṢẞŤŢṬŦÞÚÙÛÜǓŬŪŨŰŮŲỤƯẂẀŴẄǷÝỲŶŸȲỸƳŹŻŽẒŕřŗſśŝšşșṣßťţṭŧþúùûüǔŭūũűůųụưẃẁŵẅƿýỳŷÿȳỹƴźżžẓ]{1,12}"
regex_comparison_match = "[A-Za-z0-9/_=,']"

# DEFAULT SETTINGS FOR SIM
iterations = 10000
target_error = 0.100
threads = 2
calculate_scale_factors = 0


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
    randomi = " \"html=" + name + "-" + randomlause + ".html\"\""
    execution = ' \"armory=eu,%s,%s\"' % (realm, name)
    complete = path + execution + randomi
    name_compared = name_compared

    #Threading:
    global finished
    global finished_thread_name
    global amount_in_queue

    if itemcompare1 or itemcompare2:
        # User wants to compare items
        try:
            lock.acquire()  # Thread starts waiting for its turn
            if scaling:
                # User wants to compare items AND get stat scaling
                call("cmd /C %s hosted_html=1 iterations=%s target_error=%s "
                     "threads=%s calculate_scale_factors=1 copy=%s %s %s" %
                (complete, iterations, target_error,
                 threads, name_compared, itemcompare1,
                itemcompare2))

            else:
                # User wants to compare and NOT get scaling
                call("cmd /C %s hosted_html=1 iterations=%s target_error=%s "
                     "threads=%s calculate_scale_factors=%s copy=%s %s %s" %
                 (complete, iterations, target_error,
                  threads, calculate_scale_factors, name_compared, itemcompare1,
                 itemcompare2))

        except Exception as e:
            return render_template('frontcontent.html',
                                   error=e, realms=realms)

        finally:
            lock.release()

    if not (itemcompare1 or itemcompare2):
        # User does NOT want to compare with items
        try:
            lock.acquire()
            if scaling:
                # User wants to get stats scaling
                call("cmd /C %s hosted_html=1 iterations=10000 "
                     "target_error=0.050 threads=4 calculate_scale_factors=1" % complete)


            else:
                # User only wants to run a simple sim with default settings
                call("cmd /C %s hosted_html=1 iterations=%s target_error=%s threads=%s" %
                    (complete, iterations, target_error, threads))

        except Exception as e:
            return render_template('frontcontent.html',
                                   error=e, realms=realms)

        finally:
            lock.release()  # Always release thread lock no matter what happens

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
            return render_template('frontcontent.html',
                                   error="Item compare error.",
                                   realms=realms)
        if not process_input(name, realm):
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
            logger.info("%s - - New thread starting for %s, name: %s "
                        % (request.remote_addr, name, th.name))
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


# API's for last finished thread statuses and queue status:
@app.route('/status')
def thread_status():
    return jsonify(dict(status=(finished_thread_name if finished else 'running')))


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
        app.run(host='0.0.0.0', port=2302)
