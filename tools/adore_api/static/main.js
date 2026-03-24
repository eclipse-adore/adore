function showTab(tabName) {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));

    document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

class ScenarioManager {
    constructor() {
        this.currentStatus = 'idle';
        this.currentBagStatus = 'idle';
        this.currentModelCheckStatus = 'idle';
        this.currentModelCheckRunId = null;
        this.logUpdateInterval = null;
        this.statusUpdateInterval = null;
        this.positionsUpdateInterval = null;
        this.bagUpdateInterval = null;
        this.modelCheckUpdateInterval = null;
        this.runningNodesUpdateInterval = null;
        this.isEditingLoop = false;
        this.loopUpdateTimeout = null;
        this.codeEditor = null;
        this.usingTextarea = false;
        this.availableTopics = [];
        this.scenarios = [];
        this.selectedScenario = '';
        this.waitingForModelCheck = false;
        this.initializeElements();
        this.loadApiReference();
        this.initializeCodeEditor();
        this.initializeScenarioSearch();
        this.loadScenarios();
        this.loadTopics();
        this.startUpdateIntervals();
    }

    initializeCodeEditor() {
        try {
            const defaultContent = `
from launch import LaunchDescription
import os
import sys
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
from scenario_helpers.simulated_vehicle import create_simulated_vehicle_nodes
from scenario_helpers.simulated_vehicle import Position
from scenario_helpers.visualizer import create_visualization_nodes

start_position = Position(lat_long=(52.314562, 10.560474), psi=0.0)
goal_position = Position(lat_long=(52.313533, 10.560554))

def generate_launch_description():
    launch_file_dir = os.path.dirname(os.path.realpath(__file__))
    map_image_folder = os.path.abspath(os.path.join(launch_file_dir, "../assets/maps/"))
    map_folder = os.path.abspath(os.path.join(launch_file_dir, "../assets/tracks/"))
    vehicle_param = os.path.abspath(os.path.join(launch_file_dir, "../assets/vehicle_params/"))
    map_file = map_folder + "/de_bs_borders_wfs.r2sr"
    vehicle_model_file = vehicle_param + "/NGC.json"

    return LaunchDescription([
        *create_visualization_nodes(
            whitelist=["ego_vehicle"],
            asset_folder=map_image_folder,
            use_center_ego=True
        ),
        *create_simulated_vehicle_nodes(
            namespace="ego_vehicle",
            start_position=start_position,
            goal_position=goal_position,
            map_file=map_file,
            model_file=vehicle_model_file,
            controllable=True,
            optinlc_route_following=True,
            v2x_id=0,
            vehicle_id=0,
            controller=1,
            debug=False,
            composable=False
        )
    ])`;

            this.codeEditor = CodeMirror(document.getElementById('codeEditor'), {
                mode: 'python',
                theme: 'monokai',
                lineNumbers: true,
                matchBrackets: true,
                autoCloseBrackets: true,
                indentUnit: 4,
                indentWithTabs: false,
                lineWrapping: true,
                tabSize: 4,
                value: defaultContent
            });

            setTimeout(() => {
                if (this.codeEditor && this.codeEditor.getValue() === defaultContent) {
                    this.codeEditor.refresh();
                    this.codeEditor.focus();
                } else {
                    throw new Error('CodeMirror validation failed');
                }
            }, 100);

        } catch (error) {
            console.error('CodeMirror failed to initialize:', error);
            this.useFallbackTextarea();
        }
    }

    useFallbackTextarea() {
        document.querySelector('.code-editor-container').style.display = 'none';
        document.getElementById('scenarioTextarea').style.display = 'block';
        this.usingTextarea = true;
    }

    getValue() {
        if (this.usingTextarea) {
            return document.getElementById('scenarioTextarea').value;
        } else if (this.codeEditor) {
            return this.codeEditor.getValue();
        }
        return '';
    }

    setValue(content) {
        if (this.usingTextarea) {
            document.getElementById('scenarioTextarea').value = content;
        } else if (this.codeEditor) {
            this.codeEditor.setValue(content);
        }
    }

    async loadApiReference() {
        try {
            const response = await fetch('/api_reference.md');
            const markdownText = await response.text();
            const htmlContent = this.simpleMarkdownToHtml(markdownText);

            document.getElementById('api-reference-content').innerHTML = htmlContent;
            document.getElementById('api-reference-content').style.display = 'block';
            document.getElementById('api-reference-loading').style.display = 'none';

        } catch (error) {
            console.error('Failed to load API reference:', error);
            document.getElementById('api-reference-loading').innerHTML = 
                '<p style="color: #dc3545;">Failed to load API reference. Please check if api_reference.md exists.</p>';
        }
    }

    simpleMarkdownToHtml(markdown) {
        return markdown
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/```json\n([\s\S]*?)```/g, '<div class="api-endpoint"><pre><code class="param-list">$1</code></pre></div>')
            .replace(/```([\s\S]*?)```/g, '<pre><code class="param-list">$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.*)$/gm, '<p>$1</p>')
            .replace(/<p><\/p>/g, '')
            .replace(/<p>(<h[1-6]>.*<\/h[1-6]>)<\/p>/g, '$1')
            .replace(/<p>(<ul>.*<\/ul>)<\/p>/gs, '$1')
            .replace(/<p>(<div.*<\/div>)<\/p>/gs, '$1')
            .replace(/<strong>GET<\/strong>/g, '<span class="api-method method-get">GET</span>')
            .replace(/<strong>POST<\/strong>/g, '<span class="api-method method-post">POST</span>')
            .replace(/<code>\/api\/([^<]+)<\/code>/g, '<span class="api-url">/api/$1</span>');
    }

    initializeScenarioSearch() {
        const searchInput = document.getElementById('scenarioSearchInput');
        const dropdown = document.getElementById('scenarioDropdown');

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            this.filterScenarios(query);
        });

        searchInput.addEventListener('focus', () => {
            this.showDropdown();
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.scenario-search')) {
                this.hideDropdown();
            }
        });
    }

    filterScenarios(query) {
        const dropdown = document.getElementById('scenarioDropdown');
        dropdown.innerHTML = '';

        const filtered = this.scenarios.filter(scenario => 
            scenario.toLowerCase().includes(query)
        );

        if (filtered.length === 0) {
            dropdown.innerHTML = '<div class="scenario-option" style="color: #6c757d; font-style: italic;">No scenarios found</div>';
        } else {
            filtered.forEach(scenario => {
                const option = document.createElement('div');
                option.className = 'scenario-option';
                option.textContent = scenario;
                option.addEventListener('click', () => {
                    this.selectScenario(scenario);
                });
                dropdown.appendChild(option);
            });
        }

        this.showDropdown();
    }

    selectScenario(scenario) {
        this.selectedScenario = scenario;
        document.getElementById('scenarioSearchInput').value = scenario;
        this.hideDropdown();
    }

    showDropdown() {
        const dropdown = document.getElementById('scenarioDropdown');
        if (dropdown.children.length > 0) {
            dropdown.style.display = 'block';
        }
    }

    hideDropdown() {
        document.getElementById('scenarioDropdown').style.display = 'none';
    }

    initializeElements() {
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.bagStatusIndicator = document.getElementById('bagStatusIndicator');
        this.bagStatusText = document.getElementById('bagStatusText');
        this.loopMode = document.getElementById('loopMode');
        this.loopDelay = document.getElementById('loopDelay');
        this.loopRuntime = document.getElementById('loopRuntime');
        this.startBtn = document.getElementById('startBtn');
        this.restartBtn = document.getElementById('restartBtn');
        this.haltBtn = document.getElementById('haltBtn');
        this.runCustomBtn = document.getElementById('runCustomBtn');
        this.haltCustomBtn = document.getElementById('haltCustomBtn');
        this.logContainer = document.getElementById('logContainer');
        this.bagLogContainer = document.getElementById('bagLogContainer');
        this.scenarioContentToggle = document.getElementById('scenarioContentToggle');
        this.scenarioContentDiv = document.getElementById('scenarioContentDiv');
        this.scenarioContent = document.getElementById('scenarioContent');
        this.scenarioName = document.getElementById('scenarioName');
        this.saveBtn = document.getElementById('saveBtn');
        this.copySelectedBtn = document.getElementById('copySelectedBtn');
        this.clearEditorBtn = document.getElementById('clearEditorBtn');
        this.applyPositionsBtn = document.getElementById('applyPositionsBtn');
        this.storedPositionsInfo = document.getElementById('storedPositionsInfo');
        this.clearPositionsBtn = document.getElementById('clearPositionsBtn');
        this.runningNodesInfo = document.getElementById('runningNodesInfo');
        this.runningNodesCount = document.getElementById('runningNodesCount');

        this.bagDuration = document.getElementById('bagDuration');
        this.recordAllTopics = document.getElementById('recordAllTopics');
        this.topicsSelectionContainer = document.getElementById('topicsSelectionContainer');
        this.topicsContainer = document.getElementById('topicsContainer');
        this.startBagBtn = document.getElementById('startBagBtn');
        this.stopBagBtn = document.getElementById('stopBagBtn');
        this.refreshTopicsBtn = document.getElementById('refreshTopicsBtn');
        this.bagRecordingsToggle = document.getElementById('bagRecordingsToggle');
        this.bagRecordingsDiv = document.getElementById('bagRecordingsDiv');
        this.bagRecordingsList = document.getElementById('bagRecordingsList');

        this.modelCheckEnabled = document.getElementById('modelCheckEnabled');
        this.modelCheckConfig = document.getElementById('modelCheckConfig');
        this.modelCheckStatusIndicator = document.getElementById('modelCheckStatusIndicator');
        this.modelCheckStatusText = document.getElementById('modelCheckStatusText');
        this.modelCheckResultsWidget = document.getElementById('modelCheckResultsWidget');
        this.modelCheckSummary = document.getElementById('modelCheckSummary');
        this.modelCheckPropositions = document.getElementById('modelCheckPropositions');
        this.modelCheckLogContainer = document.getElementById('modelCheckLogContainer');
        this.cancelModelCheckBtn = document.getElementById('cancelModelCheckBtn');
        this.downloadModelCheckBtn = document.getElementById('downloadModelCheckBtn');

        this.startBtn.addEventListener('click', () => this.startScenario());
        this.restartBtn.addEventListener('click', () => this.restartScenario());
        this.haltBtn.addEventListener('click', () => this.haltAll());
        this.runCustomBtn.addEventListener('click', () => this.runScenarioFromEditor());
        this.haltCustomBtn.addEventListener('click', () => this.haltAll());
        this.saveBtn.addEventListener('click', () => this.saveScenario());
        this.copySelectedBtn.addEventListener('click', () => this.copySelectedScenario());
        this.clearEditorBtn.addEventListener('click', () => this.clearEditor());
        this.applyPositionsBtn.addEventListener('click', () => this.applyStoredPositions());
        this.clearPositionsBtn.addEventListener('click', () => this.clearStoredPositions());

        this.loopMode.addEventListener('change', () => this.toggleLoopMode());
        this.loopDelay.addEventListener('input', () => this.onLoopInputChange());
        this.loopRuntime.addEventListener('input', () => this.onLoopInputChange());

        this.loopDelay.addEventListener('focus', () => this.isEditingLoop = true);
        this.loopDelay.addEventListener('blur', () => this.isEditingLoop = false);
        this.loopRuntime.addEventListener('focus', () => this.isEditingLoop = true);
        this.loopRuntime.addEventListener('blur', () => this.isEditingLoop = false);

        this.startBagBtn.addEventListener('click', () => this.startBagRecording());
        this.stopBagBtn.addEventListener('click', () => this.stopBagRecording());
        this.refreshTopicsBtn.addEventListener('click', () => this.loadTopics());
        this.recordAllTopics.addEventListener('change', () => this.toggleTopicsSelection());

        this.cancelModelCheckBtn.addEventListener('click', () => this.cancelModelCheck());
        this.downloadModelCheckBtn.addEventListener('click', () => this.downloadModelCheckResults());

        this.scenarioContentToggle.addEventListener('click', () => {
            this.scenarioContentDiv.style.display = 
                this.scenarioContentDiv.style.display === 'block' ? 'none' : 'block';
        });

        this.bagRecordingsToggle.addEventListener('click', () => {
            this.bagRecordingsDiv.style.display = 
                this.bagRecordingsDiv.style.display === 'block' ? 'none' : 'block';
            if (this.bagRecordingsDiv.style.display === 'block') {
                this.updateBagRecordingsList();
            }
        });
    }

    getSafetyGradeInfo(safetyGrade) {
        if (!safetyGrade) return null;
        
        const parts = safetyGrade.split(',').map(p => p.trim());
        if (parts.length !== 2) return null;
        
        return {
            us: parts[0].toUpperCase(),
            eu: parseFloat(parts[1])
        };
    }

    createSafetyGradeBadge(grade, type) {
        const badge = document.createElement('div');
        badge.className = 'grade-badge';
        
        if (type === 'us') {
            badge.textContent = grade;
            badge.classList.add(`grade-us-${grade.toLowerCase()}`);
        } else {
            badge.textContent = grade.toString();
            badge.classList.add(`grade-eu-${Math.floor(grade)}`);
        }
        
        return badge;
    }

    async loadTopics() {
        try {
            const response = await fetch('/api/topic/list');
            const data = await response.json();

            if (data.success) {
                this.availableTopics = data.system_topics || [];
                this.updateTopicsDisplay();
            }
        } catch (error) {
            console.error('Failed to load topics:', error);
        }
    }

    updateTopicsDisplay() {
        const container = this.topicsContainer;
        container.innerHTML = '';

        if (this.availableTopics.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: #6c757d;">No topics found</div>';
            return;
        }

        this.availableTopics.forEach(topic => {
            const label = document.createElement('label');
            label.className = 'topic-checkbox';
            label.innerHTML = `
                <input type="checkbox" value="${topic}">
                ${topic}
            `;
            container.appendChild(label);
        });
    }

    toggleTopicsSelection() {
        const showSelection = !this.recordAllTopics.checked;
        this.topicsSelectionContainer.style.display = showSelection ? 'block' : 'none';
    }

    getSelectedTopics() {
        if (this.recordAllTopics.checked) {
            return [];
        }

        const checkboxes = this.topicsContainer.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async startBagRecording() {
        const duration = parseInt(this.bagDuration.value) || null;
        const topics = this.getSelectedTopics();

        try {
            const response = await fetch('/api/bag/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration, topics })
            });

            const result = await response.json();
            if (result.success) {
                console.log('Bag recording started successfully');
            } else {
                alert(`Failed to start bag recording: ${result.message}`);
            }
        } catch (error) {
            console.error('Failed to start bag recording:', error);
            alert('Failed to start bag recording');
        }
    }

    async stopBagRecording() {
        try {
            const response = await fetch('/api/bag/stop', { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                console.log('Bag recording stopped successfully');
                alert(`Recording saved: ${result.relative_path}`);
            } else {
                alert(`Failed to stop bag recording: ${result.message}`);
            }
        } catch (error) {
            console.error('Failed to stop bag recording:', error);
            alert('Failed to stop bag recording');
        }
    }

    async cancelModelCheck() {
        if (!this.currentModelCheckRunId) {
            return;
        }

        try {
            const response = await fetch(`/api/model_check/cancel/${this.currentModelCheckRunId}`, {
                method: 'POST'
            });

            const result = await response.json();
            if (result.message) {
                console.log('Model checking cancelled');
            }
        } catch (error) {
            console.error('Failed to cancel model checking:', error);
        }
    }

    async downloadModelCheckResults() {
        if (!this.currentModelCheckRunId) {
            return;
        }

        try {
            const url = `/api/model_check/result/${this.currentModelCheckRunId}/download`;
            const link = document.createElement('a');
            link.href = url;
            link.download = `model_check_results_${this.currentModelCheckRunId}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Failed to download model check results:', error);
        }
    }

    async updateBagStatus() {
        try {
            const response = await fetch('/api/bag/status');
            const status = await response.json();

            this.currentBagStatus = status.status;
            this.bagStatusIndicator.className = `status-indicator status-${status.status}`;

            let statusText = `Status: ${status.status.toUpperCase()}`;
            if (status.bag_name) {
                statusText += ` - ${status.bag_name}`;
            }
            if (status.runtime) {
                statusText += ` (${Math.round(status.runtime)}s)`;
            }
            this.bagStatusText.textContent = statusText;

            this.updateBagButtonStates();
        } catch (error) {
            console.error('Failed to update bag status:', error);
            this.bagStatusText.textContent = 'Status unavailable';
        }
    }

    async updateModelCheckStatus() {
        try {
            const statusResponse = await fetch('/api/scenario/status');
            if (!statusResponse.ok) {
                console.error(`Failed to fetch scenario status: ${statusResponse.status}`);
                this.modelCheckStatusText.textContent = 'Status unavailable';
                return;
            }
            
            const scenarioStatus = await statusResponse.json();
            
            if (scenarioStatus.current_model_check_run_id !== undefined && 
                scenarioStatus.current_model_check_run_id !== null) {
                this.currentModelCheckRunId = scenarioStatus.current_model_check_run_id;
            }
            
            if (this.currentModelCheckRunId !== null && this.currentModelCheckRunId !== undefined) {
                const response = await fetch(`/api/model_check/result/${this.currentModelCheckRunId}`);
    
                if (response.ok) {
                    const result = await response.json();
    
                    this.currentModelCheckStatus = result.status || 'unknown';
                    this.modelCheckStatusIndicator.className = `status-indicator status-${this.currentModelCheckStatus}`;
    
                    let statusText = `Status: ${this.currentModelCheckStatus.toUpperCase()}`;
                    if (result.run_id !== undefined) {
                        statusText += ` - Run ${result.run_id}`;
                    }
                    if (result.mode) {
                        statusText += ` (${result.mode})`;
                    }
                    
                    this.modelCheckStatusText.textContent = statusText;
    
                    let logContent = '';
                    if (this.currentModelCheckStatus === 'running' || this.currentModelCheckStatus === 'pending') {
                        try {
                            const logResponse = await fetch(`/api/model_check/result/${this.currentModelCheckRunId}/log/current`);
                            if (logResponse.ok) {
                                const logData = await logResponse.json();
                                logContent = logData.log_content || result.stdout || '';
                            } else {
                                logContent = result.stdout || '';
                            }
                        } catch (e) {
                            logContent = result.stdout || '';
                        }
                    } else {
                        logContent = result.stdout || '';
                    }
                    
                    this.updateModelCheckLog(logContent);
    
                    const isCompleted = (this.currentModelCheckStatus.toLowerCase() === 'completed');
                    if (result.results && isCompleted) {
                        this.updateModelCheckResults(result.results);
                        this.modelCheckResultsWidget.style.display = 'block';
                    } else if (isCompleted) {
                        this.modelCheckResultsWidget.style.display = 'none';
                    } else {
                        this.modelCheckResultsWidget.style.display = 'none';
                    }
    
                    this.updateModelCheckButtonStates();
                } else if (response.status === 404) {
                    this.currentModelCheckRunId = null;
                    this.currentModelCheckStatus = 'idle';
                    this.modelCheckStatusIndicator.className = 'status-indicator status-idle';
                    this.modelCheckStatusText.textContent = 'Idle';
                    this.modelCheckResultsWidget.style.display = 'none';
                    this.updateModelCheckButtonStates();
                    this.updateModelCheckLog('No model checking output');
                } else {
                    console.error(`Model check API error: ${response.status} ${response.statusText}`);
                    this.modelCheckStatusText.textContent = `API Error: ${response.status}`;
                    this.updateModelCheckLog(`API Error: ${response.status} ${response.statusText}`);
                }
            } else {
                this.currentModelCheckStatus = 'idle';
                this.modelCheckStatusIndicator.className = 'status-indicator status-idle';
                this.modelCheckStatusText.textContent = 'Idle';
                this.modelCheckResultsWidget.style.display = 'none';
                this.updateModelCheckButtonStates();
                this.updateModelCheckLog('No model checking output');
            }
        } catch (error) {
            console.error('Exception in updateModelCheckStatus:', error);
            this.modelCheckStatusText.textContent = 'Error fetching status';
            this.updateModelCheckLog(`Error fetching model check status: ${error.message}`);
        }
    }
    
    updateModelCheckLog(content) {
        if (content && content.trim().length > 0) {
            this.modelCheckLogContainer.textContent = content;
        } else {
            this.modelCheckLogContainer.textContent = 'No model checking output available';
        }
        this.modelCheckLogContainer.scrollTop = this.modelCheckLogContainer.scrollHeight;
    }
updateModelCheckResults(results) {
        try {
            if (!results) {
                this.modelCheckResultsWidget.style.display = 'none';
                return;
            }
    
            this.modelCheckResultsWidget.style.display = 'block';
    
            const summary = results.SUMMARY || {};
            const summaryHtml = `
                <div class="summary-stat">
                    <span class="value">${summary.total_propositions || 0}</span>
                    <span class="label">Total</span>
                </div>
                <div class="summary-stat">
                    <span class="value">${summary.passed || 0}</span>
                    <span class="label">Passed</span>
                </div>
                <div class="summary-stat">
                    <span class="value">${summary.failed || 0}</span>
                    <span class="label">Failed</span>
                </div>
                <div class="summary-stat">
                    <span class="value">${((summary.success_rate || 0) * 100).toFixed(1)}%</span>
                    <span class="label">Success Rate</span>
                </div>
                <div class="summary-stat">
                    <span class="value">${summary.overall_result || 'N/A'}</span>
                    <span class="label">Overall</span>
                </div>
            `;
            this.modelCheckSummary.innerHTML = summaryHtml;
    
            let propositionsHtml = '';
            let propositionCount = 0;
            Object.keys(results).forEach(key => {
                if (key !== 'SUMMARY') {
                    const proposition = results[key];
                    propositionsHtml += this.createPropositionHtml(key, proposition);
                    propositionCount++;
                }
            });
            
            if (propositionCount === 0) {
                propositionsHtml = '<div style="text-align: center; color: #6c757d; padding: 20px;">No proposition results found</div>';
            }
            
            this.modelCheckPropositions.innerHTML = propositionsHtml;
        } catch (error) {
            console.error('Error updating model check results:', error);
            this.modelCheckResultsWidget.style.display = 'none';
        }
    }

    createPropositionHtml(key, proposition) {
        const status = proposition.status ? proposition.status.toLowerCase() : 'unknown';
        const cssClass = status === 'pass' ? 'proposition-pass' : 
                       status === 'fail' ? 'proposition-fail' : 
                       status === 'no_data' ? 'proposition-no-data' : 'proposition-error';

        const statusClass = status === 'pass' ? 'status-pass' : 
                           status === 'fail' ? 'status-fail' : 
                           status === 'no_data' ? 'status-no-data' : 'status-error';

        const description = proposition.description || {};
        const title = description.title || key.replace(/_/g, ' ');
        const desc = description.description || 'No description available';
        const rationale = description.safety_rationale || 'Safety rationale not provided';
        const formulaDesc = proposition.formula_description || 'Formula description not available';
        const group = proposition.group || 'unknown';

        let safetyGradeHtml = '';
        if (proposition.statistics && proposition.statistics.safety_grade) {
            const gradeInfo = this.getSafetyGradeInfo(proposition.statistics.safety_grade);
            if (gradeInfo) {
                safetyGradeHtml = `
                    <div class="safety-grade">
                        <span class="grade-label">Safety Grade:</span>
                        <div class="grade-badge grade-us-${gradeInfo.us.toLowerCase()}">${gradeInfo.us}</div>
                        <div class="grade-badge grade-eu-${Math.floor(gradeInfo.eu)}">${gradeInfo.eu.toFixed(1)}</div>
                    </div>
                `;
            }
        }

        const technicalDetails = `
            <div class="proposition-technical-content">
                <strong>Technical ID:</strong> ${key}<br>
                <strong>Formula Type:</strong> ${proposition.formula_type || 'N/A'}<br>
                <strong>Threshold:</strong> ${proposition.threshold !== undefined ? proposition.threshold : 'N/A'}<br>
                <strong>States Analyzed:</strong> ${proposition.states_analyzed || 'N/A'}<br>
                <strong>Kripke States:</strong> ${proposition.kripke_states || 'N/A'}<br>
                <strong>Result Value:</strong> ${proposition.result !== undefined ? proposition.result : 'N/A'}
                ${proposition.error ? `<br><strong>Error:</strong> ${proposition.error}` : ''}
            </div>
        `;

        return `
            <div class="proposition-item ${cssClass}">
                <div class="group-indicator">${group.replace(/_/g, ' ')}</div>
                <div class="proposition-header">
                    <h4 class="proposition-title">${title}</h4>
                    <span class="proposition-status ${statusClass}">${status.toUpperCase()}</span>
                </div>
                <div class="proposition-description">${desc}</div>
                <div class="proposition-rationale">
                    <strong>Why this matters:</strong> ${rationale}
                </div>
                <div class="proposition-formula">
                    <strong>Requirement:</strong> ${formulaDesc}
                </div>
                ${safetyGradeHtml}
                <div class="proposition-technical">
                    ${technicalDetails}
                </div>
            </div>
        `;
    }

    updateBagButtonStates() {
        const isRecording = this.currentBagStatus === 'recording';
        this.startBagBtn.disabled = isRecording;
        this.stopBagBtn.disabled = !isRecording;
    }

    updateModelCheckButtonStates() {
        const isRunning = this.currentModelCheckStatus === 'running' || this.currentModelCheckStatus === 'pending';
        const hasResults = this.currentModelCheckStatus === 'completed' && this.currentModelCheckRunId !== null;

        this.cancelModelCheckBtn.disabled = !isRunning;
        this.downloadModelCheckBtn.disabled = !hasResults;
    }

    async updateBagLog() {
        try {
            const response = await fetch('/api/bag/output?lines=50');
            const data = await response.json();

            this.bagLogContainer.textContent = data.output || 'No bag recording output';
            this.bagLogContainer.scrollTop = this.bagLogContainer.scrollHeight;
        } catch (error) {
            console.error('Failed to update bag log:', error);
        }
    }

    async updateBagRecordingsList() {
        try {
            const response = await fetch('/api/bag/list');
            const data = await response.json();

            if (data.success && data.bags.length > 0) {
                let html = '<h4>Recorded Bag Files:</h4>';
                data.bags.forEach(bag => {
                    html += `
                        <div style="background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 4px;">
                            <strong>${bag.name}</strong><br>
                            <small>Path: ${bag.relative_path}</small><br>
                            <small>Created: ${bag.created} | Size: ${bag.size_mb.toFixed(2)} MB</small>
                        </div>
                    `;
                });
                this.bagRecordingsList.innerHTML = html;
            } else {
                this.bagRecordingsList.innerHTML = '<p>No bag recordings found</p>';
            }
        } catch (error) {
            console.error('Failed to update bag recordings list:', error);
            this.bagRecordingsList.innerHTML = '<p>Failed to load bag recordings</p>';
        }
    }

    async updateRunningNodes() {
        try {
            const response = await fetch('/api/ros2/nodes/running');
            const data = await response.json();

            if (data.running_nodes && data.running_nodes.length > 0) {
                this.runningNodesCount.textContent = data.count;

                let html = '';
                data.running_nodes.forEach(node => {
                    html += `<div class="node-item">${node}</div>`;
                });
                this.runningNodesInfo.innerHTML = html;
            } else {
                this.runningNodesCount.textContent = '0';
                this.runningNodesInfo.innerHTML = '<div class="no-running-nodes">No running nodes</div>';
            }
        } catch (error) {
            console.error('Failed to update running nodes:', error);
            this.runningNodesCount.textContent = '?';
            this.runningNodesInfo.innerHTML = '<div class="no-running-nodes">Failed to load nodes</div>';
        }
    }

    async runScenarioFromEditor() {
        const content = this.getValue().trim();
        if (!content) {
            alert('Please enter launch file content in the Scenario Editor');
            return;
        }

        if (this.currentStatus === 'running') {
            const shouldHalt = confirm(
                'A scenario is currently running. Do you want to halt the current scenario and run the scenario from the editor?\n\n' +
                'Click "OK" to halt current scenario and run from editor.\n' +
                'Click "Cancel" to keep current scenario running.'
            );

            if (!shouldHalt) {
                return;
            }

            try {
                const haltResponse = await fetch('/api/scenario/halt', { method: 'POST' });
                const haltResult = await haltResponse.json();

                if (!haltResult.success) {
                    alert(`Failed to halt current scenario: ${haltResult.message}`);
                    return;
                }

                await new Promise(resolve => setTimeout(resolve, 2000));

            } catch (error) {
                console.error('Failed to halt current scenario:', error);
                alert('Failed to halt current scenario. Please try again.');
                return;
            }
        }

        try {
            const response = await fetch('/api/scenario/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    scenario: content, 
                    is_file: false,
                    model_check_enabled: this.modelCheckEnabled.checked,
                    model_check_config: this.modelCheckConfig.value
                })
            });

            const result = await response.json();
            if (result.success) {
                const originalText = this.runCustomBtn.textContent;
                this.runCustomBtn.textContent = 'Scenario Started!';
                this.runCustomBtn.style.backgroundColor = '#28a745';
                setTimeout(() => {
                    this.runCustomBtn.textContent = originalText;
                    this.runCustomBtn.style.backgroundColor = '';
                }, 2000);
            } else {
                alert(`Failed to start scenario from editor: ${result.message}`);
            }
        } catch (error) {
            console.error('Failed to run scenario from editor:', error);
            alert('Failed to run scenario from editor. Please check the content and try again.');
        }
    }

    clearEditor() {
        if (confirm('Are you sure you want to clear the Scenario Editor? This action cannot be undone.')) {
            const defaultContent = `# Welcome to the Scenario Editor
# Write your ROS2 launch file content here...

# Example ROS2 Launch File:
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Add your nodes here
    ])
`;
            this.setValue(defaultContent);
        }
    }

    onLoopInputChange() {
        this.isEditingLoop = true;

        if (this.loopUpdateTimeout) {
            clearTimeout(this.loopUpdateTimeout);
        }

        this.loopUpdateTimeout = setTimeout(() => {
            this.isEditingLoop = false;
            this.toggleLoopMode();
        }, 1000);
    }

    async loadScenarios() {
        try {
            const response = await fetch('/api/scenario/get');
            const data = await response.json();

            this.scenarios = data.scenarios || [];
            this.filterScenarios('');
        } catch (error) {
            console.error('Failed to load scenarios:', error);
        }
    }

    async startScenario() {
        const scenario = this.selectedScenario;
        if (!scenario) {
            alert('Please select a scenario');
            return;
        }

        if (this.currentStatus === 'running') {
            const shouldHalt = confirm(
                'A scenario is currently running. Do you want to halt the current scenario and start the selected scenario?\n\n' +
                'Click "OK" to halt current scenario and start selected scenario.\n' +
                'Click "Cancel" to keep current scenario running.'
            );

            if (!shouldHalt) {
                return;
            }

            try {
                await fetch('/api/scenario/halt', { method: 'POST' });
                await new Promise(resolve => setTimeout(resolve, 2000));
            } catch (error) {
                console.error('Failed to halt current scenario:', error);
                alert('Failed to halt current scenario. Please try again.');
                return;
            }
        }

        try {
            const response = await fetch('/api/scenario/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    scenario, 
                    is_file: true,
                    model_check_enabled: this.modelCheckEnabled.checked,
                    model_check_config: this.modelCheckConfig.value
                })
            });

            const result = await response.json();
            if (!result.success) {
                alert(result.message);
            }
        } catch (error) {
            console.error('Failed to start scenario:', error);
        }
    }

    async restartScenario() {
        try {
            const response = await fetch('/api/scenario/restart', { method: 'POST' });
            const result = await response.json();
            if (!result.success) {
                alert(result.message);
            }
        } catch (error) {
            console.error('Failed to restart scenario:', error);
        }
    }

    async haltAll() {
        if (confirm('This will halt all ROS2 processes. Continue?')) {
            try {
                const response = await fetch('/api/scenario/halt', { method: 'POST' });
                const result = await response.json();
                if (!result.success) {
                    alert(result.message);
                }
            } catch (error) {
                console.error('Failed to halt scenarios:', error);
            }
        }
    }

    async saveScenario() {
        const name = this.scenarioName.value.trim();
        const content = this.getValue().trim();

        if (!name || !content) {
            alert('Please enter both scenario name and content');
            return;
        }

        try {
            const response = await fetch('/api/scenario/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, content })
            });

            const result = await response.json();
            if (result.success) {
                alert(result.message);
                this.scenarioName.value = '';
                this.loadScenarios();
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error('Failed to save scenario:', error);
            alert('Failed to save scenario');
        }
    }

    async copySelectedScenario() {
        const selectedScenario = this.selectedScenario;

        if (!selectedScenario) {
            alert('Please select a scenario first');
            return;
        }

        try {
            const response = await fetch(`/api/scenario/content/${encodeURIComponent(selectedScenario)}`);
            const result = await response.json();

            if (result.success) {
                this.setValue(result.content);
                alert(`Selected scenario "${selectedScenario}" copied to Scenario Editor`);
            } else {
                alert(result.message || 'Failed to copy selected scenario');
            }
        } catch (error) {
            console.error('Failed to copy selected scenario:', error);
            alert('Failed to copy selected scenario');
        }
    }

    async applyStoredPositions() {
        try {
            const response = await fetch('/api/positions/get');
            const positions = await response.json();

            if (!positions.start && !positions.goal) {
                alert('No stored positions found. Use the Goal Picker tab to set positions.');
                return;
            }

            let content = this.getValue();
            let lines = content.split('\n');
            let modified = false;

            if (positions.start) {
                const psi = positions.start.psi !== undefined ? positions.start.psi.toFixed(3) : '0.0';
                const newStartLine = `start_position = Position(lat_long=(${positions.start.lat.toFixed(6)}, ${positions.start.lng.toFixed(6)}), psi=${psi})`;

                let startFound = false;
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].trim().startsWith('start_position = Position(')) {
                        lines[i] = newStartLine;
                        startFound = true;
                        modified = true;
                        break;
                    }
                }

                if (!startFound) {
                    lines.unshift(newStartLine);
                    modified = true;
                }
            }

            if (positions.goal) {
                const newGoalLine = `goal_position = Position(lat_long=(${positions.goal.lat.toFixed(6)}, ${positions.goal.lng.toFixed(6)}))`;

                let goalFound = false;
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].trim().startsWith('goal_position = Position(')) {
                        lines[i] = newGoalLine;
                        goalFound = true;
                        modified = true;
                        break;
                    }
                }

                if (!goalFound) {
                    lines.push(newGoalLine);
                    modified = true;
                }
            }

            if (modified) {
                this.setValue(lines.join('\n'));
                alert('Stored positions applied to Scenario Editor');
            }

        } catch (error) {
            console.error('Failed to apply stored positions:', error);
            alert('Failed to apply stored positions');
        }
    }

    async clearStoredPositions() {
        if (confirm('Clear all stored positions?')) {
            try {
                const response = await fetch('/api/positions/clear', { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    alert('Stored positions cleared!');
                    this.updateStoredPositions();
                } else {
                    alert('Failed to clear stored positions');
                }
            } catch (error) {
                console.error('Failed to clear stored positions:', error);
                alert('Failed to clear stored positions');
            }
        }
    }

    async updateStoredPositions() {
        try {
            const response = await fetch('/api/positions/get');
            const positions = await response.json();
    
            if (!positions.start && !positions.goal) {
                this.storedPositionsInfo.innerHTML = '<div class="no-stored-positions">No positions stored</div>';
                return;
            }
    
            let html = '';
    
            if (positions.start) {
                const utm = positions.start.utm;
                const psi = positions.start.psi !== undefined ? positions.start.psi.toFixed(3) : '0.0';
                html += `
                    <div class="position-item">
                        <strong>🟢 Start Position:</strong><br>
                        Lat/Long: ${positions.start.lat.toFixed(6)}, ${positions.start.lng.toFixed(6)}<br>
                        UTM: ${utm.easting.toLocaleString()}m E, ${utm.northing.toLocaleString()}m N<br>
                        Zone: ${utm.zone}${utm.hemisphere}<br><br>
                        <strong>Python Code:</strong><br>
                        <code style="font-size: 10px; background: #f4f4f4; padding: 2px; border-radius: 2px; display: block; margin: 2px 0;">
                        start_position = Position(lat_long=(${positions.start.lat.toFixed(6)}, ${positions.start.lng.toFixed(6)}), psi=${psi})
                        </code>
                        <code style="font-size: 10px; background: #f4f4f4; padding: 2px; border-radius: 2px; display: block; margin: 2px 0;">
                        start_position = Position(utm=(${utm.easting.toFixed(1)}, ${utm.northing.toFixed(1)}, ${utm.zone}, '${utm.hemisphere}'), psi=${psi})
                        </code>
                    </div>
                `;
            }
    
            if (positions.goal) {
                const utm = positions.goal.utm;
                html += `
                    <div class="position-item">
                        <strong>🔴 Goal Position:</strong><br>
                        Lat/Long: ${positions.goal.lat.toFixed(6)}, ${positions.goal.lng.toFixed(6)}<br>
                        UTM: ${utm.easting.toLocaleString()}m E, ${utm.northing.toLocaleString()}m N<br>
                        Zone: ${utm.zone}${utm.hemisphere}<br><br>
                        <strong>Python Code:</strong><br>
                        <code style="font-size: 10px; background: #f4f4f4; padding: 2px; border-radius: 2px; display: block; margin: 2px 0;">
                        goal_position = Position(lat_long=(${positions.goal.lat.toFixed(6)}, ${positions.goal.lng.toFixed(6)}))
                        </code>
                        <code style="font-size: 10px; background: #f4f4f4; padding: 2px; border-radius: 2px; display: block; margin: 2px 0;">
                        goal_position = Position(utm=(${utm.easting.toFixed(1)}, ${utm.northing.toFixed(1)}, ${utm.zone}, '${utm.hemisphere}'))
                        </code>
                    </div>
                `;
            }
    
            html += `
                <div class="position-item" style="background: #e3f2fd; border-left-color: #2196f3;">
                    <strong>📘 Note:</strong> <code>psi</code> parameter represents vehicle start rotation in radians.<br>
                    <small>0.0 = facing East, π/2 = North, π = West, 3π/2 = South</small>
                </div>
            `;
    
            this.storedPositionsInfo.innerHTML = html;
    
        } catch (error) {
            console.error('Failed to update stored positions:', error);
        }
    }

    async toggleLoopMode() {
        const enabled = this.loopMode.checked;
        const delay = parseInt(this.loopDelay.value) || 0;
        const runtime = parseInt(this.loopRuntime.value) || 60;
        const modelCheckEnabled = this.modelCheckEnabled.checked;
        const modelCheckConfig = this.modelCheckConfig.value || 'config/default.yaml';

        try {
            const response = await fetch('/api/scenario/loop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    enabled, 
                    delay, 
                    runtime,
                    model_check_enabled: modelCheckEnabled,
                    model_check_config: modelCheckConfig
                })
            });

            const result = await response.json();
            if (!result.success) {
                alert(result.message);
            }
        } catch (error) {
            console.error('Failed to toggle loop mode:', error);
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/scenario/status');
            const status = await response.json();

            this.currentStatus = status.status;
            this.statusIndicator.className = `status-indicator status-${status.status}`;
            this.waitingForModelCheck = status.waiting_for_model_check || false;

            let statusText = `Status: ${status.status.toUpperCase()}`;
            if (status.scenario) {
                statusText += ` - ${status.scenario}`;
            }
            if (status.runtime) {
                statusText += ` (${Math.round(status.runtime)}s)`;
            }
            if (this.waitingForModelCheck) {
                statusText += ' - Waiting for model check completion';
            }
            this.statusText.textContent = statusText;

            if (!this.isEditingLoop) {
                this.loopMode.checked = status.loop_mode;
                this.loopDelay.value = status.loop_delay;
                this.loopRuntime.value = status.default_runtime;
                this.modelCheckEnabled.checked = status.model_check_enabled !== false;
                this.modelCheckConfig.value = status.model_check_config || 'config/default.yaml';
            }

            if (status.scenario_content) {
                this.scenarioContent.textContent = status.scenario_content;
            }

            this.updateButtonStates();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    }

    updateButtonStates() {
        const isRunning = this.currentStatus === 'running';
        this.startBtn.disabled = isRunning;
        this.restartBtn.disabled = !isRunning;

        if (isRunning) {
            this.runCustomBtn.textContent = 'Replace Running Scenario';
            this.runCustomBtn.classList.remove('btn-success');
            this.runCustomBtn.classList.add('btn-warning');
        } else {
            this.runCustomBtn.textContent = 'Run Scenario from Editor';
            this.runCustomBtn.classList.remove('btn-warning');
            this.runCustomBtn.classList.add('btn-success');
        }
    }

    async updateLog() {
        try {
            const response = await fetch('/api/scenario/output?lines=100');
            const data = await response.json();

            this.logContainer.textContent = data.output;
            this.logContainer.scrollTop = this.logContainer.scrollHeight;
        } catch (error) {
            console.error('Failed to update log:', error);
        }
    }

    startUpdateIntervals() {
        this.updateStatus();
        this.updateLog();
        this.updateStoredPositions();
        this.updateBagStatus();
        this.updateBagLog();
        this.updateModelCheckStatus();
        this.updateRunningNodes();

        this.statusUpdateInterval = setInterval(() => this.updateStatus(), 1000);
        this.logUpdateInterval = setInterval(() => this.updateLog(), 2000);
        this.positionsUpdateInterval = setInterval(() => this.updateStoredPositions(), 5000);
        this.bagUpdateInterval = setInterval(() => {
            this.updateBagStatus();
            this.updateBagLog();
        }, 2000);
        this.modelCheckUpdateInterval = setInterval(() => this.updateModelCheckStatus(), 2000);
        this.runningNodesUpdateInterval = setInterval(() => this.updateRunningNodes(), 60000);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new ScenarioManager();

    const lichtblickUrl = document.getElementById('lichtblickUrl');
    if (lichtblickUrl) {
        lichtblickUrl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('lichtblickFrame').src = lichtblickUrl.value;
            }
        });
    }
});
