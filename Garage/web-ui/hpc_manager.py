import reactpy as rp
import json
import time

class HPC_Manager:
    def __init__(self):
        self.available_clusters = []
        self.current_cluster = None
        self.job_queue = []
        self.running_jobs = []
        self.completed_jobs = []
        self.load_cluster_config()
        
        # Form state
        self.job_name = "My CFD Job"
        self.num_cores = 4
        self.memory_per_core = 4
        self.walltime = 12
        self.selected_cluster_id = ""
    
    def load_cluster_config(self):
        """Load HPC cluster configurations"""
        # In a real application, this would load from a config file
        self.available_clusters = [
            {
                "id": "local",
                "name": "Local Workstation",
                "cores": 8,
                "memory": "32GB",
                "connection": "localhost"
            },
            {
                "id": "cluster1",
                "name": "University Cluster",
                "cores": 128,
                "memory": "512GB",
                "connection": "ssh://user@university-cluster.edu"
            },
            {
                "id": "cluster2",
                "name": "Cloud HPC",
                "cores": 256,
                "memory": "1TB",
                "connection": "https://cloud-hpc-api.example.com"
            }
        ]
    
    def connect_to_cluster(self, cluster_id):
        """Connect to a specific HPC cluster"""
        self.selected_cluster_id = cluster_id
        for cluster in self.available_clusters:
            if cluster["id"] == cluster_id:
                # In a real implementation, this would establish a connection
                self.current_cluster = cluster
                return True
        return False
    
    def disconnect_from_cluster(self):
        """Disconnect from the current cluster"""
        if self.current_cluster:
            # In a real implementation, this would close connections
            self.current_cluster = None
            self.selected_cluster_id = ""
            return True
        return False
    
    def submit_job(self):
        """Submit a job to the current cluster"""
        if not self.current_cluster:
            return False
        
        # Create a job object with a unique ID
        job = {
            "id": f"job_{int(time.time())}_{len(self.job_queue) + len(self.running_jobs)}",
            "name": self.job_name,
            "config": {
                "name": self.job_name,
                "cores": self.num_cores,
                "memory": self.memory_per_core,
                "walltime": self.walltime
            },
            "status": "queued",
            "submitted_time": time.time(),
            "cluster": self.current_cluster["id"]
        }
        
        self.job_queue.append(job)
        return job["id"]
    
    def check_job_status(self, job_id):
        """Check the status of a specific job"""
        # Search in all job lists
        for job_list in [self.job_queue, self.running_jobs, self.completed_jobs]:
            for job in job_list:
                if job["id"] == job_id:
                    return job["status"]
        return None
    
    def get_job_details(self, job_id):
        """Get detailed information about a job"""
        for job_list in [self.job_queue, self.running_jobs, self.completed_jobs]:
            for job in job_list:
                if job["id"] == job_id:
                    return job
        return None
    
    def cancel_job(self, job_id):
        """Cancel a queued or running job"""
        # Check job queue
        for i, job in enumerate(self.job_queue):
            if job["id"] == job_id:
                del self.job_queue[i]
                job["status"] = "cancelled"
                self.completed_jobs.append(job)
                return True
                
        # Check running jobs
        for i, job in enumerate(self.running_jobs):
            if job["id"] == job_id:
                # In a real implementation, this would send a cancel signal to the cluster
                del self.running_jobs[i]
                job["status"] = "cancelled"
                self.completed_jobs.append(job)
                return True
                
        return False
    
    # Handlers for form inputs
    def update_job_name(self, event):
        self.job_name = event["target"]["value"]
        
    def update_num_cores(self, event):
        try:
            self.num_cores = int(event["target"]["value"])
        except ValueError:
            self.num_cores = 1
            
    def update_memory_per_core(self, event):
        try:
            self.memory_per_core = int(event["target"]["value"])
        except ValueError:
            self.memory_per_core = 1
            
    def update_walltime(self, event):
        try:
            self.walltime = int(event["target"]["value"])
        except ValueError:
            self.walltime = 1
    
    def render(self):
        """Render the HPC manager UI components"""
        cluster_selector = rp.html.div(
            {"className": "cluster-selector"},
            [
                rp.html.h3("Select HPC Cluster"),
                rp.html.select(
                    {
                        "value": self.selected_cluster_id,
                        "onChange": lambda e: self.connect_to_cluster(e["target"]["value"])
                    },
                    [
                        rp.html.option({"value": ""}, "Select a cluster..."),
                        *[rp.html.option({"value": cluster["id"]}, cluster["name"]) 
                          for cluster in self.available_clusters]
                    ]
                ),
                rp.html.button(
                    {
                        "onClick": lambda e: self.disconnect_from_cluster(),
                        "disabled": not self.current_cluster,
                        "className": "disconnect-btn"
                    },
                    "Disconnect"
                )
            ]
        )
        
        job_submission = rp.html.div(
            {"className": "job-submission"},
            [
                rp.html.h3("Submit CFD Job"),
                rp.html.div(
                    {"className": "job-form"},
                    [
                        rp.html.div(
                            [
                                rp.html.label({"htmlFor": "job-name"}, "Job Name:"),
                                rp.html.input({
                                    "id": "job-name", 
                                    "type": "text", 
                                    "placeholder": "My CFD Job",
                                    "value": self.job_name,
                                    "onChange": self.update_job_name
                                })
                            ]
                        ),
                        rp.html.div(
                            [
                                rp.html.label({"htmlFor": "num-cores"}, "Number of Cores:"),
                                rp.html.input({
                                    "id": "num-cores", 
                                    "type": "number", 
                                    "min": "1", 
                                    "value": str(self.num_cores),
                                    "onChange": self.update_num_cores
                                })
                            ]
                        ),
                        rp.html.div(
                            [
                                rp.html.label({"htmlFor": "memory"}, "Memory per Core (GB):"),
                                rp.html.input({
                                    "id": "memory", 
                                    "type": "number", 
                                    "min": "1", 
                                    "value": str(self.memory_per_core),
                                    "onChange": self.update_memory_per_core
                                })
                            ]
                        ),
                        rp.html.div(
                            [
                                rp.html.label({"htmlFor": "walltime"}, "Walltime (hours):"),
                                rp.html.input({
                                    "id": "walltime", 
                                    "type": "number", 
                                    "min": "1", 
                                    "value": str(self.walltime),
                                    "onChange": self.update_walltime
                                })
                            ]
                        ),
                        rp.html.div(
                            [
                                rp.html.label({"htmlFor": "input-file"}, "Input File:"),
                                rp.html.input({"id": "input-file", "type": "file"})
                            ]
                        ),
                        rp.html.button(
                            {
                                "className": "submit-job-btn",
                                "disabled": not self.current_cluster,
                                "onClick": lambda e: self.submit_job()
                            },
                            "Submit Job"
                        )
                    ]
                )
            ]
        )
        
        job_monitor = rp.html.div(
            {"className": "job-monitor"},
            [
                rp.html.h3("Job Monitor"),
                rp.html.div(
                    {"className": "job-tabs"},
                    [
                        rp.html.button({"className": "tab-btn active"}, f"Queue ({len(self.job_queue)})"),
                        rp.html.button({"className": "tab-btn"}, f"Running ({len(self.running_jobs)})"),
                        rp.html.button({"className": "tab-btn"}, f"Completed ({len(self.completed_jobs)})")
                    ]
                ),
                rp.html.div(
                    {"className": "job-list"},
                    rp.html.table(
                        [
                            rp.html.thead(
                                rp.html.tr([
                                    rp.html.th("Job ID"),
                                    rp.html.th("Name"),
                                    rp.html.th("Status"),
                                    rp.html.th("Submitted"),
                                    rp.html.th("Actions")
                                ])
                            ),
                            rp.html.tbody([
                                rp.html.tr([
                                    rp.html.td(job["id"]),
                                    rp.html.td(job["name"]),
                                    rp.html.td(job["status"]),
                                    rp.html.td(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(job["submitted_time"]))),
                                    rp.html.td(
                                        rp.html.button(
                                            {
                                                "onClick": lambda e, j=job["id"]: self.cancel_job(j),
                                                "className": "cancel-btn"
                                            },
                                            "Cancel"
                                        )
                                    )
                                ])
                                for job in self.job_queue
                            ])
                        ]
                    ) if self.job_queue else rp.html.div("No jobs in queue")
                )
            ]
        )
        
        cluster_status = rp.html.div(
            {"className": "cluster-status"},
            [
                rp.html.h3("Cluster Status"),
                rp.html.div(
                    {"className": "status-info"},
                    [
                        rp.html.div(f"Connected to: {self.current_cluster['name']}") if self.current_cluster else
                        rp.html.div("Not connected to any cluster"),
                        rp.html.div(f"Available cores: {self.current_cluster['cores']}") if self.current_cluster else None,
                        rp.html.div(f"Available memory: {self.current_cluster['memory']}") if self.current_cluster else None
                    ]
                )
            ]
        )
        
        return rp.html.div(
            {"className": "hpc-manager"},
            [cluster_selector, cluster_status, job_submission, job_monitor]
        )
