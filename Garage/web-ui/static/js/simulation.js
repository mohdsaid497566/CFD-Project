/**
 * Simulation page functionality
 */

// When the page loads
document.addEventListener('DOMContentLoaded', function() {
    // References to DOM elements
    const simulationSelect = document.getElementById('simulationSelect');
    const simulationName = document.getElementById('simulationName');
    const saveSimBtn = document.getElementById('saveSimBtn');
    const runSimBtn = document.getElementById('runSimBtn');
    const simLog = document.getElementById('sim-log');
    const simStatus = document.getElementById('sim-status');
    const currentSim = document.getElementById('current-sim');
    
    // Handle simulation selection change
    if (simulationSelect) {
        simulationSelect.addEventListener('change', function() {
            if (this.value) {
                // If an existing simulation is selected, disable the name field
                simulationName.value = this.options[this.selectedIndex].text;
                simulationName.disabled = true;
                
                // Load simulation data
                loadSimulationData(this.value);
            } else {
                // If "Create new" is selected, enable the name field and clear it
                simulationName.value = '';
                simulationName.disabled = false;
                
                // Reset form to default values
                document.getElementById('simulationForm').reset();
            }
        });
    }
    
    // Handle save simulation button click
    if (saveSimBtn) {
        saveSimBtn.addEventListener('click', function() {
            // Validate form
            if (!simulationName.value) {
                alert('Please enter a simulation name');
                simulationName.focus();
                return;
            }
            
            // Get form data
            const formData = new FormData(document.getElementById('simulationForm'));
            const simData = {};
            for (const [key, value] of formData.entries()) {
                simData[key] = value;
            }
            
            // Send data to server
            fetch('/api/save-simulation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(simData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Simulation saved successfully');
                    // Reload page to refresh simulation list
                    location.reload();
                } else {
                    alert('Error saving simulation: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error saving simulation');
            });
        });
    }
    
    // Handle run simulation button click
    if (runSimBtn) {
        runSimBtn.addEventListener('click', function() {
            // Show loading state
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Starting...';
            
            // Get selected simulation file
            const simFile = simulationSelect.value;
            
            // Update simulation status
            currentSim.textContent = simFile || simulationName.value || 'Unnamed simulation';
            simStatus.textContent = 'Initializing...';
            simLog.innerHTML = '<p>Starting simulation...</p>';
            
            // Call API to run simulation
            fetch('/api/run-simulation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    simulation_file: simFile,
                    simulation_name: simulationName.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    simStatus.textContent = 'Running';
                    simLog.innerHTML += '<p>' + data.message + '</p>';
                    
                    // Simulate progress updates (in a real app, this would come from a websocket or polling)
                    startProgressSimulation();
                } else {
                    simStatus.textContent = 'Error';
                    simLog.innerHTML += '<p class="text-danger">Error: ' + data.message + '</p>';
                }
            })
            .catch(error => {
                simStatus.textContent = 'Error';
                simLog.innerHTML += '<p class="text-danger">Error: ' + error + '</p>';
            })
            .finally(() => {
                // Reset button state
                this.disabled = false;
                this.innerHTML = 'Run Simulation';
            });
        });
    }
    
    // Function to load simulation data
    function loadSimulationData(simulationFile) {
        fetch('/api/get-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                simulation_file: simulationFile
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Populate form with simulation data
                const simData = data.simulation;
                for (const key in simData) {
                    const element = document.getElementById(key);
                    if (element) {
                        element.value = simData[key];
                    }
                }
            } else {
                alert('Error loading simulation: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading simulation');
        });
    }
    
    // For demonstration purposes - simulate progress updates
    window.startProgressSimulation = function() {
        let progress = 0;
        let seconds = 0;
        const progressBar = document.querySelector('.progress-bar');
        const timeElm = document.getElementById('sim-time');
        const logElm = document.getElementById('sim-log');
        
        const interval = setInterval(() => {
            progress += 1;
            seconds += 3;
            
            if (progress <= 100) {
                progressBar.style.width = progress + '%';
                progressBar.setAttribute('aria-valuenow', progress);
                progressBar.textContent = progress + '%';
                
                // Format time as hours:minutes:seconds
                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                const secs = seconds % 60;
                timeElm.textContent = `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                
                // Add log messages at certain points
                if (progress === 10) {
                    logElm.innerHTML += '<p>Mesh generation started...</p>';
                } else if (progress === 30) {
                    logElm.innerHTML += '<p>Mesh generation complete. 245,678 cells created.</p>';
                } else if (progress === 40) {
                    logElm.innerHTML += '<p>Initializing flow field...</p>';
                } else if (progress === 50) {
                    logElm.innerHTML += '<p>Starting solver iterations...</p>';
                } else if (progress === 95) {
                    logElm.innerHTML += '<p>Finalizing results...</p>';
                } else if (progress === 100) {
                    logElm.innerHTML += '<p class="text-success">Simulation completed successfully!</p>';
                    simStatus.textContent = 'Completed';
                    clearInterval(interval);
                }
                
                // Scroll to bottom of log
                logElm.scrollTop = logElm.scrollHeight;
            } else {
                clearInterval(interval);
            }
        }, 300);
    };
});
