from flask import Flask, request, jsonify
import json,uuid,os,getpass,sys,datetime, time
import zmq, _thread


app = Flask(__name__)

extensions = { "C":"c", "Python":"py", "Bash":"sh" }
user_storage = "/zfs-storage/students/"
job_storage = "/zfs-storage/jobs/"
job_status_dir = job_storage + ".jobs"
scheduler_host = "localhost"
#scheduler_host = "192.168.43.77"

sub_port = "6555"
publish_port = "5556"
topic = "job_created"

context = zmq.Context()

# ZMQ socket to listen for job updates [subscriber]
socket_sub = context.socket(zmq.SUB)
socket_sub.connect ("tcp://%s:%s" %(scheduler_host, sub_port))
topicfilter = "job_update"
socket_sub.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

#ZMQ Socket to create job by sending job_data
socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://*:%s" % publish_port)


#Job update listener thread
def listen_for_job_updates(thread_name, index):
    while True:
        string = socket_sub.recv().decode("UTF-8")
        topic, job_data = string.split(" ",1)
        print("Job update recieved: ",topic,job_data)
        job_data = json.loads(job_data)

        dir_name = user_storage + job_data["user"] + "/.jobs/" + job_data["jobID"]
        while not os.path.isdir(dir_name):
            pass

        file_name = dir_name + "/" + job_data["jobID"]
        while not os.path.exists(file_name):
            time.sleep(1)
            pass

        job_data_file = open(file_name,"w")
        job_data_file.write(job_data["status"]+ " " + job_data["updated_at"])
        job_data_file.close()

        if job_data["status"] != "in-progress":
            os.system("cp " + job_storage + job_data["jobID"] + "/*  " + user_storage + job_data["user"] + "/.jobs/" + job_data["jobID"] + "/")


def cp(source, destination):
    cp_path = "/bin/cp"
    cmd = [cp_path, source, destination ]
    os.execv(cp_path,cmd)


def publish_job(job_data):
    print("Publishing Job: %s %s" % (topic, job_data))
    socket_pub.send_string("%s %s" % (topic, job_data))


@app.route("/")
def main():
    return "Hello Client!!! Read the help for creating job by using 'job --help' command"


@app.route("/tools")
def tools():
    if request.method == "GET":
        return jsonify(["C", "Python", "Bash"])

@app.route("/create_job",methods=["POST"])
def create_job():
    if request.method == "POST":
        data = request.json
        data["jobID"] = str(uuid.uuid4())
        error = 0

        #Making copy of job source code
        print(data["file_path"])
        source =  user_storage + data["user"] + "/" + data["file_path"]
        os.mkdir(job_storage + data["jobID"])
        destination = job_storage + data["jobID"] + "/" + data["jobID"] + "." + extensions[data["job_tool"]]

        childpid = os.fork()
        if childpid == 0:
            cp(source,destination)

        exit_code = os.waitpid(0, 0)[1]

        data["file_path"] = destination
        data["created_at"] = str(datetime.datetime.now())
        data["updated_at"] = str(datetime.datetime.now())

        if exit_code==0:
            data["status"] = "created"
            publish_job(json.dumps(data))
        else:
            data["status"] = "failed"
            data["details"] = "Source file not found"

        #print(data)

        return jsonify(data)



if __name__ == "__main__":
    if getpass.getuser()!="root":
        print("Needs root priviledges")
        sys.exit()

    _thread.start_new_thread(listen_for_job_updates, ("JOB_UPDATE_LISTENER",0))
    app.run(host= '0.0.0.0')
