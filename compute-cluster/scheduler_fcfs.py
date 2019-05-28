import queue as q
import sys, zmq, time, _thread, json, datetime, os

STDIN = 0
STDOUT = 1

user = os.environ["USER"]

job_storage_mount_point = "/zfs-storage/jobs/"
job_creator_host = "localhost"
sub_port = "5556"
publish_port = "6555"
topic = "job_update"

images_cmds = { "Bash":["bash:latest","bash"], "C":["gcc:latest","gcc"], "Python":["jfloff/alpine-python:2.7","python"] }


if len(sys.argv) > 1:
    port =  sys.argv[1]
    int(port)

# Socket to talk to server [subscriber]
context = zmq.Context()
socket_sub = context.socket(zmq.SUB)
socket_sub.connect ("tcp://%s:%s" %(job_creator_host, sub_port))
topicfilter = "job_created"
socket_sub.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

#ZMQ Socket to send job updates
socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://*:%s" % publish_port)


#Job listener thread
def listen_for_jobs(thread_name, index):
    while True:
        string = socket_sub.recv().decode("UTF-8")
        topic, job_data = string.split(" ",1)
        print("Job arrived: ",topic, job_data)
        q.enqueue(job_data)

#Job status updater
def update_job_status(job_data):
    print("Updating job status: %s %s" % (topic, job_data))
    socket_pub.send_string("%s %s" % (topic, job_data))


#Job executor
def execute(job_data):

    pipein, pipeout = os.pipe()
    job_dir = job_storage_mount_point + job_data["jobID"]
    job_file = job_data["file_path"][len(job_dir):]

    childpid = os.fork()
    if childpid == 0:
        os.close(pipein)
        os.dup2(pipeout, STDOUT)

        docker_bin_path = "/usr/bin/docker"
        #print(job_dir)
        #print(job_file)
        if job_data["job_tool"] == "C":
            cmd = [ docker_bin_path, 'run', '-v', job_dir + ':/job', images_cmds[job_data["job_tool"]][0], images_cmds[job_data["job_tool"]][1], "-o", "/job/a.out", "/job"+job_file ]
        else:
            cmd = [ docker_bin_path, 'run', '-v', job_dir + ':/job', images_cmds[job_data["job_tool"]][0], images_cmds[job_data["job_tool"]][1], "/job"+job_file ]
        os.execv(docker_bin_path,cmd)

    #For mapping stdout of child using pipe to stdin of parent
    os.close(pipeout)
    os.dup2(pipein, STDIN)

    #writing stdout output to file
    stdout_file = job_dir + "/stdout"
    stdout_file = open(stdout_file,"w")
    try:
        dump = input()
    except EOFError:
        dump = ""
    stdout_file.write(dump)
    stdout_file.close()

    return os.waitpid(0, 0)[1]



_thread.start_new_thread(listen_for_jobs, ("JOB_LISTENER",0))

def fcfs():
    while True:
        job_data = q.dequeue()

        if job_data:
            job_data = json.loads(job_data)

            job_data["status"] = "in-progress"
            job_data["updated_at"] = str(datetime.datetime.now())
            update_job_status(json.dumps(job_data))

            exit_code = execute(job_data)

            if exit_code == 0:
                job_data["status"] = "completed"
            else:
                job_data["status"] = "failed"
            job_data["updated_at"] = str(datetime.datetime.now())
            update_job_status(json.dumps(job_data))

        time.sleep(5)

if __name__=="__main__":
    if user !="root":
        print("Needs root priviledges!")
        sys.exit()
    fcfs()
