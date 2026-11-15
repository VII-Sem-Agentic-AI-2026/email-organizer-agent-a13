document.addEventListener('DOMContentLoaded', () => {
    
    const processBtn = document.getElementById('process-inbox-btn');
    const draftModal = document.getElementById('draft-modal');
    const cancelDraftBtn = document.getElementById('cancel-draft-btn');
    const saveDraftBtn = document.getElementById('save-draft-btn');

    // Snooze modal elements
    const snoozeModal = document.getElementById('snooze-modal');
    const cancelSnoozeBtn = document.getElementById('cancel-snooze-btn');
    const confirmSnoozeBtn = document.getElementById('confirm-snooze-btn');
    const snoozeIntervalSelect = document.getElementById('snooze-interval-select');
    const customSnoozeGroup = document.getElementById('custom-snooze-group');
    const customSnoozeMinutes = document.getElementById('custom-snooze-minutes');
    const defaultDelaySelect = document.getElementById('default-reminder-delay');

    let currentDrafts = [];
    
    processBtn.addEventListener('click', async () => {
        processBtn.disabled = true;
        processBtn.textContent = "Processing...";
        processBtn.classList.remove('pulse');
        
        try {
            const res = await fetch('/api/process', { method: 'POST' });
            if(res.ok) {
                await loadState();
                showToast("Inbox processed successfully!", "success");
            } else {
                showToast("Failed to process inbox.", "error");
            }
        } catch(e) {
            showToast("Error: " + e.message, "error");
        }
        
        processBtn.disabled = false;
        processBtn.textContent = "Process Inbox";
    });
    
    cancelDraftBtn.addEventListener('click', () => {
        draftModal.style.display = 'none';
    });
    
    saveDraftBtn.addEventListener('click', async () => {
        const id = document.getElementById('edit-draft-id').value;
        const subject = document.getElementById('edit-draft-subject').value;
        const body = document.getElementById('edit-draft-body').value;
        
        try {
            await fetch(`/api/drafts/${id}/edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subject, body })
            });
            draftModal.style.display = 'none';
            await loadState();
            showToast("Draft updated successfully.", "success");
        } catch(e) {
            showToast("Error saving draft: " + e.message, "error");
        }
    });

    if (cancelSnoozeBtn) {
        cancelSnoozeBtn.addEventListener('click', () => {
            snoozeModal.style.display = 'none';
        });
    }

    if (snoozeIntervalSelect) {
        snoozeIntervalSelect.addEventListener('change', () => {
            if (snoozeIntervalSelect.value === 'custom') {
                customSnoozeGroup.style.display = 'block';
            } else {
                customSnoozeGroup.style.display = 'none';
            }
        });
    }

    if (confirmSnoozeBtn) {
        confirmSnoozeBtn.addEventListener('click', async () => {
            const reminderId = document.getElementById('snooze-reminder-id').value;
            let minutes = snoozeIntervalSelect.value;
            if (minutes === 'custom') {
                minutes = customSnoozeMinutes.value;
                if (!minutes || parseInt(minutes) <= 0) {
                    showToast("Please enter a valid positive number of minutes.", "error");
                    return;
                }
            }

            try {
                const res = await fetch(`/api/reminders/${reminderId}/snooze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ delay_minutes: parseInt(minutes) })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    snoozeModal.style.display = 'none';
                    showToast(`⏰ Reminder snoozed for ${minutes} minutes.`, "success");
                    await loadState();
                } else {
                    showToast("Failed to snooze reminder: " + (data.error || "Unknown error"), "error");
                }
            } catch(e) {
                showToast("Error snoozing reminder: " + e.message, "error");
            }
        });
    }

    if (defaultDelaySelect) {
        defaultDelaySelect.addEventListener('change', async () => {
            const val = parseInt(defaultDelaySelect.value);
            try {
                const res = await fetch('/api/reminders/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ default_delay_minutes: val })
                });
                if (res.ok) {
                    showToast(`Default reminder delay set to ${val} minutes.`, "success");
                }
            } catch(e) {
                console.error("Failed to update reminder config", e);
            }
        });
    }
    
    async function loadState() {
        try {
            const res = await fetch('/api/state');
            const state = await res.json();
            currentDrafts = state.drafts || [];

            renderMetrics(state.metrics);
            renderDiagnostics(state.diagnostics);
            renderPipeline(state.pipeline_status);
            renderInbox(state.inbox);
            renderDrafts(state.drafts);
            renderTasks(state.tasks);
            renderMeetings(state.meetings);
            renderReminders(state.reminders, state.reminder_config);
            renderReminderAlerts(state.reminders, state.drafts);
            renderFollowUps(state.follow_ups);
            renderAuditLog(state.audit_log);
        } catch(e) {
            console.error("Failed to load state", e);
        }
    }
    
    function renderMetrics(metrics) {
        const container = document.getElementById('metrics-container');
        if (!container || !metrics) return;
        container.innerHTML = `
            <div class="card">
                <h3>Drafts Reviewed</h3>
                <div class="value">${metrics.total_drafts_reviewed}</div>
            </div>
            <div class="card">
                <h3>Pending Review</h3>
                <div class="value">${metrics.pending_review_count}</div>
            </div>
            <div class="card">
                <h3>Approved</h3>
                <div class="value" style="color: var(--success)">${metrics.approved_count}</div>
            </div>
            <div class="card">
                <h3>Rejected</h3>
                <div class="value" style="color: var(--danger)">${metrics.rejected_count}</div>
            </div>
            <div class="card">
                <h3>Follow-up Completion</h3>
                <div class="value">${metrics.follow_up_completion_rate}%</div>
            </div>
            <div class="card">
                <h3>Avg Review Time</h3>
                <div class="value">${metrics.average_review_time_seconds}</div>
            </div>
        `;
    }
    
    function renderDiagnostics(diagnostics) {
        const container = document.getElementById('diagnostics-list');
        if (!diagnostics || !container) return;
        
        const groqErrorStr = diagnostics.groq_error ? `<br><span style="font-size:0.7rem; color:#f87171;">${diagnostics.groq_error.split('.')[0]}</span>` : '';
        
        container.innerHTML = `
            <div class="pipeline-item">
                <span class="pipeline-label">Gmail API</span>
                <span class="pipeline-status ${diagnostics.gmail_status === 'Connected' ? 'success' : 'failed'}">${diagnostics.gmail_status}</span>
            </div>
            <div class="pipeline-item" style="flex-direction: column; align-items: flex-start;">
                <div style="display:flex; justify-content:space-between; width:100%;">
                    <span class="pipeline-label">Groq (openai/gpt-oss-20b)</span>
                    <span class="pipeline-status ${diagnostics.groq_status === 'Connected' ? 'success' : (diagnostics.groq_status === 'Fallback' ? 'fallback' : 'pending')}">${diagnostics.groq_status}</span>
                </div>
                ${groqErrorStr}
            </div>
            <div class="pipeline-item">
                <span class="pipeline-label">Calendar API</span>
                <span class="pipeline-status ${diagnostics.calendar_status === 'Connected' ? 'success' : 'pending'}">${diagnostics.calendar_status}</span>
            </div>
            <div class="pipeline-item">
                <span class="pipeline-label">Thread Grounding</span>
                <span class="pipeline-status success">${diagnostics.thread_grounding}</span>
            </div>
            <div class="pipeline-item">
                <span class="pipeline-label">Auto-send</span>
                <span class="pipeline-status pending">${diagnostics.auto_send}</span>
            </div>
            <div class="pipeline-item">
                <span class="pipeline-label">Pending Approvals</span>
                <span class="pipeline-status ${diagnostics.pending_approvals > 0 ? 'fallback' : 'success'}">${diagnostics.pending_approvals}</span>
            </div>
            <div class="pipeline-item">
                <span class="pipeline-label">Last Pipeline Run</span>
                <span class="pipeline-status" style="font-size: 0.8rem">${diagnostics.last_run ? new Date(diagnostics.last_run).toLocaleTimeString() : 'Never'}</span>
            </div>
        `;
    }

    function renderPipeline(pipeline) {
        const container = document.getElementById('pipeline-list');
        if (!pipeline || !container) return;
        
        let html = '';
        for (const [step, status] of Object.entries(pipeline)) {
            let statusClass = 'pending';
            let displayStatus = status;
            if (status === '✓') {
                statusClass = 'success';
                displayStatus = '✓ SUCCESS';
            }
            if (status === 'PENDING_REVIEW') {
                statusClass = 'success';
            }
            if (status === 'FAILED' || status.includes('REJECTED')) {
                statusClass = 'failed';
            }
            if (status === 'FALLBACK') {
                statusClass = 'fallback';
                displayStatus = '⚠ FALLBACK';
            }
            
            html += `
                <div class="pipeline-item">
                    <span class="pipeline-label">${step}</span>
                    <span class="pipeline-status ${statusClass}">${displayStatus}</span>
                </div>
            `;
        }
        container.innerHTML = html;
    }
    
    function renderInbox(inbox) {
        const container = document.getElementById('inbox-list');
        if(!container) return;
        if(!inbox || inbox.length === 0) {
            container.innerHTML = "<p>No emails to display.</p>";
            return;
        }
        
        container.innerHTML = inbox.map(email => `
            <div class="item-card">
                <div class="item-header">
                    <span>From: ${email.sender}</span>
                    <span class="badge ${email.priority.toLowerCase()}">${email.priority}</span>
                </div>
                <div class="item-title">${email.subject}</div>
                <div class="item-body">
                    Type: ${email.email_type} | Category: ${email.sender_category}
                    ${email.action_items && email.action_items.length ? '<br>⚡ Contains Action Items' : ''}
                </div>
                ${email.evidence && email.evidence.length > 0 ? `
                <div class="evidence-box">
                    <strong style="color:#10b981;">GROUNDING: GROUNDED</strong><br><br>
                    ${email.evidence.map(ev => `
                        <div style="margin-bottom:8px; border-left:2px solid rgba(255,255,255,0.2); padding-left:8px;">
                            <strong>Subject:</strong> ${ev.subject || 'Unknown'}<br>
                            <strong>Sender:</strong> ${ev.sender || 'Unknown'}<br>
                            <strong>Relevance:</strong> ${ev.relevance || 'N/A'}<br>
                            <strong>Content:</strong> <span style="opacity:0.8">${(ev.content || '').substring(0, 100)}...</span>
                        </div>
                    `).join('')}
                </div>
                ` : `
                <div class="evidence-box">
                    <strong style="color:#ef4444;">GROUNDING: REJECTED</strong><br>
                    Reason: No relevant prior message found.
                </div>
                `}
            </div>
        `).join('');
    }
    
    function renderDrafts(drafts) {
        const container = document.getElementById('drafts-list');
        if(!container) return;
        const activeDrafts = (drafts || []).filter(d => d.state !== 'sent' && d.state !== 'rejected');
        if(!activeDrafts || activeDrafts.length === 0) {
            container.innerHTML = "<p>No pending drafts.</p>";
            return;
        }
        
        container.innerHTML = activeDrafts.map(draft => `
            <div class="item-card" id="draft-card-${draft.id}">
                <div class="item-header">
                    <span>To: ${draft.recipient}</span>
                    <div>
                        ${draft.source ? `<span class="badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8; margin-right: 6px;">${draft.source}</span>` : ''}
                        <span class="badge ${draft.state.toLowerCase()}">${draft.state} (v${draft.version})</span>
                    </div>
                </div>
                <div class="item-title">${draft.subject}</div>
                <div class="item-body" style="white-space: pre-wrap;">${draft.body}</div>
                <div class="item-actions">
                    ${draft.state === 'draft' ? `
                        <button class="secondary-btn" onclick="openEditModal('${draft.id}', decodeURIComponent('${encodeURIComponent(draft.subject)}'), decodeURIComponent('${encodeURIComponent(draft.body)}'))">Edit</button>
                        <button class="success-btn" onclick="actDraft('${draft.id}', 'approve')">Approve</button>
                        <button class="danger-btn" onclick="actDraft('${draft.id}', 'reject')">Reject</button>
                    ` : ''}
                    ${draft.state === 'approved' ? `
                        <button class="primary-btn" onclick="actDraft('${draft.id}', 'send')">Send</button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
    
    function renderTasks(tasks) {
        const container = document.getElementById('tasks-list');
        if(!container) return;
        const activeTasks = (tasks || []).filter(task => task.status !== 'completed');
        if(!activeTasks || activeTasks.length === 0) {
            container.innerHTML = "<p>No pending action items.</p>";
            return;
        }
        
        container.innerHTML = activeTasks.map(task => `
            <div class="item-card">
                <div class="item-header">
                    <span>Source: ${task.source_email}</span>
                    <span class="badge ${task.status === 'completed' ? 'completed' : 'pending'}">${task.status}</span>
                </div>
                <div class="item-title">${task.description}</div>
                <div class="item-body">
                    Assigned: ${task.assigned_to || 'Unassigned'} | Due: ${task.deadline || 'None'}
                    ${task.confidence !== undefined && task.confidence !== null ? `<br>Confidence: ${Math.round(task.confidence * 100)}%` : ''}
                </div>
                ${task.status === 'pending' ? `
                    <div class="item-actions">
                        <button class="success-btn" onclick="completeTask('${task.id}')">Complete</button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    // FEATURE 1: Render Meeting Requests with explicit approval, slot confirmation, and Google Calendar event creation
    function renderMeetings(meetings) {
        const container = document.getElementById('meetings-list');
        if(!container) return;

        // Preserve input values and active focus across periodic auto-refresh
        const preservedInputs = {};
        const activeEl = document.activeElement;
        const activeId = (activeEl && activeEl.id && activeEl.id.startsWith('slot-')) ? activeEl.id : null;
        let cursorStart = null;
        let cursorEnd = null;
        if (activeId && typeof activeEl.selectionStart === 'number') {
            cursorStart = activeEl.selectionStart;
            cursorEnd = activeEl.selectionEnd;
        }

        container.querySelectorAll('input[id^="slot-"], select[id^="slot-"]').forEach(el => {
            if (el.value) {
                preservedInputs[el.id] = el.value;
            }
        });

        const pendingMeetings = (meetings || []).filter(m => m.status === 'pending');
        if(!pendingMeetings || pendingMeetings.length === 0) {
            container.innerHTML = "<p>No pending meeting requests.</p>";
            return;
        }
        
        container.innerHTML = pendingMeetings.map(m => {
            const isMissingDateTime = m.missing_date_or_time || (!m.proposed_date && !m.proposed_time);
            
            return `
            <div class="item-card" id="meeting-card-${m.id}">
                <div class="item-header">
                    <span>From: ${m.sender}</span>
                    <span class="badge ${m.status.toLowerCase()}">${m.status}</span>
                </div>
                <div class="item-title">${m.title || m.subject}</div>
                <div class="item-body">
                    <strong>Attendees:</strong> ${(m.attendees && m.attendees.length) ? m.attendees.join(', ') : m.sender}<br>
                    <strong>Duration:</strong> ${m.duration_minutes || 30} minutes<br>
                    <strong>Requested Time:</strong> ${m.proposed_date || 'Unspecified'}${m.proposed_time ? ', ' + m.proposed_time : ''}${m.requested_slot_status === 'BUSY' ? ' — <span style="color:#ef4444; font-weight:bold;">BUSY</span>' : ''}
                    ${m.description ? `<br><strong>Details:</strong> <span style="opacity:0.8;">${m.description}</span>` : ''}
                </div>

                ${isMissingDateTime ? `
                    <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; font-size: 0.85rem; color: #fcd34d;">
                        ⚠️ <strong>Action Required:</strong> Date or time was not specified in the email. Please select a suitable slot from Google Calendar availability before approving.
                    </div>
                ` : ''}

                <div style="margin-top: 10px; margin-bottom: 8px;">
                    <label style="font-size: 0.85rem; font-weight: 600; display: block; margin-bottom: 4px;">
                        ${m.requested_slot_status === 'BUSY' ? 'Calendar Busy. Suggested Free Slots:' : 'Select Proposed Slot for Google Calendar:'}
                    </label>
                    ${(m.available_slots && m.available_slots.length > 0) ? `
                        <select id="slot-${m.id}" class="input-field" style="width: 100%; padding: 7px; margin-bottom: 8px;">
                            ${m.available_slots.map(s => `<option value="${s}">${s}</option>`).join('')}
                        </select>
                    ` : `
                        <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px;">No automatic slots available. Select date & time:</div>
                        <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                            <input type="datetime-local" id="slot-picker-${m.id}" class="input-field" style="flex: 1; padding: 7px; color: #f8fafc;" onchange="window.syncSlotPicker('${m.id}', this.value)">
                            <input type="text" id="slot-${m.id}" class="input-field" placeholder="e.g. 2026-11-20 03:00 PM" style="flex: 1; padding: 7px;">
                        </div>
                    `}
                </div>
                <div class="item-actions">
                    <button class="success-btn" id="btn-approve-${m.id}" onclick="approveMeetingEvent('${m.id}')">Approve Event</button>
                    <button class="danger-btn" id="btn-reject-${m.id}" onclick="rejectMeetingEvent('${m.id}')">Reject Event</button>
                </div>
            </div>
            `;
        }).join('');

        // Restore preserved input values
        Object.keys(preservedInputs).forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.value = preservedInputs[id];
            }
        });

        // Restore active focus and cursor position
        if (activeId) {
            const elToFocus = document.getElementById(activeId);
            if (elToFocus) {
                elToFocus.focus();
                if (cursorStart !== null && typeof elToFocus.setSelectionRange === 'function') {
                    try {
                        elToFocus.setSelectionRange(cursorStart, cursorEnd);
                    } catch(e) {}
                }
            }
        }
    }

    // FEATURE 2: Render Reminder Alerts (Due High-Priority Reminders)
    function renderReminderAlerts(reminders, drafts) {
        const container = document.getElementById('reminder-banner-container');
        if (!container) return;

        if (!reminders || reminders.length === 0) {
            container.innerHTML = '';
            return;
        }

        const dueReminders = reminders.filter(r => r.is_due && (r.status === 'pending' || r.status === 'snoozed'));

        if (dueReminders.length === 0) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = dueReminders.map(r => `
            <div class="reminder-alert-card" id="reminder-alert-${r.id}">
                <div class="reminder-alert-header">
                    <span class="reminder-alert-title">🔔 Important Email Reminder!</span>
                    <span class="badge ${r.priority.toLowerCase()}">${r.priority} PRIORITY</span>
                </div>
                <div class="reminder-alert-body">
                    You have an unanswered high-priority email.<br><br>
                    <strong>From:</strong> ${r.sender}<br>
                    <strong>Subject:</strong> ${r.subject}<br>
                    <strong>Priority:</strong> ${r.priority}
                    ${r.snooze_count > 0 ? `<br><small style="color: #cbd5e1;">(Snoozed ${r.snooze_count} time${r.snooze_count > 1 ? 's' : ''} previously)</small>` : ''}
                    <br><br>
                    <em>Would you like to reply now?</em>
                </div>
                <div class="reminder-alert-actions">
                    <button class="primary-btn" onclick="replyNowReminder('${r.id}', '${r.email_id}')">Reply Now</button>
                    <button class="secondary-btn snooze-dropdown-btn" onclick="openSnoozeModal('${r.id}')">Snooze ⏱️</button>
                    <button class="success-btn" onclick="handleReminder('${r.id}')">Mark as Handled ✓</button>
                </div>
            </div>
        `).join('');
    }

    // FEATURE 2: Render Reminders list in panel
    function renderReminders(reminders, config) {
        const container = document.getElementById('reminders-list');
        if (config && defaultDelaySelect && config.default_delay_minutes) {
            defaultDelaySelect.value = String(config.default_delay_minutes);
        }

        if (!container) return;
        const activeReminders = (reminders || []).filter(r => r.status === 'pending' || r.status === 'snoozed');
        if (!activeReminders || activeReminders.length === 0) {
            container.innerHTML = "<p>No active priority reminders.</p>";
            return;
        }

        container.innerHTML = activeReminders.map(r => {
            const remindDate = new Date(r.remind_at);
            const isDue = r.is_due;
            return `
            <div class="item-card" id="reminder-item-${r.id}">
                <div class="item-header">
                    <span>From: ${r.sender}</span>
                    <div>
                        <span class="badge ${r.priority.toLowerCase()}">${r.priority}</span>
                        <span class="badge ${r.status.toLowerCase()}">${r.status}</span>
                    </div>
                </div>
                <div class="item-title">${r.subject}</div>
                <div class="item-body">
                    <strong>Scheduled For:</strong> ${remindDate.toLocaleString()} 
                    ${isDue ? ' <span style="color:#ef4444; font-weight:bold;">(DUE NOW)</span>' : ''}<br>
                    <strong>Snoozed:</strong> ${r.snooze_count} time${r.snooze_count === 1 ? '' : 's'}
                    ${r.handled_at ? `<br><strong>Handled At:</strong> ${new Date(r.handled_at).toLocaleString()}` : ''}
                </div>
                ${(r.status === 'pending' || r.status === 'snoozed') ? `
                    <div class="item-actions">
                        <button class="primary-btn" onclick="replyNowReminder('${r.id}', '${r.email_id}')">Reply Now</button>
                        <button class="secondary-btn" onclick="openSnoozeModal('${r.id}')">Snooze</button>
                        <button class="success-btn" onclick="handleReminder('${r.id}')">Mark Handled</button>
                    </div>
                ` : ''}
            </div>
            `;
        }).join('');
    }
    
    function renderFollowUps(followups) {
        const container = document.getElementById('followups-list');
        if(!container) return;
        const activeFollowups = (followups || []).filter(f => f.status !== 'completed');
        if(!activeFollowups || activeFollowups.length === 0) {
            container.innerHTML = "<p>No pending follow-ups.</p>";
            return;
        }
        
        container.innerHTML = activeFollowups.map(f => `
            <div class="item-card">
                <div class="item-header">
                    <span>Due: ${new Date(f.reminder_at).toLocaleString()}</span>
                    <span class="badge ${f.status === 'completed' ? 'completed' : (f.is_due ? 'critical' : 'pending')}">${f.status}</span>
                </div>
                <div class="item-title">${f.email_subject}</div>
                ${f.status === 'pending' ? `
                    <div class="item-actions">
                        <button class="success-btn" onclick="completeFollowUp('${f.id}')">Complete</button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    function renderAuditLog(log) {
        const container = document.getElementById('audit-list');
        if(!container) return;
        if(!log || log.length === 0) {
            container.innerHTML = "<p>No history.</p>";
            return;
        }
        
        const reversedLog = [...log].reverse();
        
        container.innerHTML = reversedLog.map(entry => `
            <div class="item-card" style="padding: 10px;">
                <div style="font-size: 0.8rem; color: #94a3b8;">${new Date(entry.timestamp).toLocaleString()}</div>
                <div style="font-weight: 600;">${entry.actor} performed ${entry.action.toUpperCase()}</div>
                ${entry.recipient ? `<div style="font-size: 0.85rem; color: #cbd5e1;">Target: ${entry.recipient} - ${entry.subject || ''}</div>` : ''}
            </div>
        `).join('');
    }
    
    // Global functions for inline onclick handlers
    window.openEditModal = (id, subject, body) => {
        document.getElementById('edit-draft-id').value = id;
        document.getElementById('edit-draft-subject').value = subject;
        document.getElementById('edit-draft-body').value = body;
        draftModal.style.display = 'flex';
    };
    
    window.actDraft = async (id, action) => {
        try {
            const res = await fetch(`/api/drafts/${id}/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reviewer: "Faculty User" })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showToast(`Draft action '${action}' completed.`, 'success');
            } else {
                showToast(`Error: ${data.error || 'Action failed'}`, 'error');
            }
            await loadState();
        } catch(e) {
            showToast(`Error performing ${action}: ` + e.message, 'error');
        }
    };
    
    window.completeTask = async (id) => {
        try {
            await fetch(`/api/tasks/${id}/complete`, { method: 'POST' });
            await loadState();
            showToast("Task completed.", "success");
        } catch(e) {
            showToast("Error completing task: " + e.message, "error");
        }
    };
    
    window.completeFollowUp = async (id) => {
        try {
            await fetch(`/api/followups/${id}/complete`, { method: 'POST' });
            await loadState();
            showToast("Follow-up completed.", "success");
        } catch(e) {
            showToast("Error completing follow-up: " + e.message, "error");
        }
    };
    
    // Synchronize native datetime-local picker with text input
    window.syncSlotPicker = (id, val) => {
        if (!val) return;
        const textEl = document.getElementById(`slot-${id}`);
        if (textEl) {
            textEl.value = val;
        }
    };

    // FEATURE 1: Explicit Calendar Event Approval
    window.approveMeetingEvent = async (id) => {
        const btn = document.getElementById(`btn-approve-${id}`);
        const slotEl = document.getElementById(`slot-${id}`);
        const pickerEl = document.getElementById(`slot-picker-${id}`);
        
        let slot = slotEl ? slotEl.value.trim() : "";
        if (!slot && pickerEl && pickerEl.value) {
            slot = pickerEl.value.trim();
        }

        if (!slot) {
            showToast('Please select or specify a time slot before approving.', 'error');
            if (slotEl) slotEl.focus();
            return;
        }

        if (btn) {
            btn.disabled = true;
            btn.textContent = "Creating Google Calendar Event...";
        }

        try {
            const res = await fetch(`/api/meetings/${id}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showToast(`✅ ${data.message}`, 'success');
            } else {
                showToast(`❌ Failed to approve event: ${data.error || 'Unknown error'}`, 'error');
            }
            await loadState();
        } catch(e) {
            showToast('Error approving calendar event: ' + e.message, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = "Approve Event";
            }
        }
    };

    // FEATURE 1: Reject Calendar Event
    window.rejectMeetingEvent = async (id) => {
        const btn = document.getElementById(`btn-reject-${id}`);
        if (btn) {
            btn.disabled = true;
        }
        try {
            const res = await fetch(`/api/meetings/${id}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showToast("Meeting event proposal rejected.", 'success');
            } else {
                showToast("Failed to reject event: " + (data.error || 'Unknown error'), 'error');
            }
            await loadState();
        } catch(e) {
            showToast("Error rejecting meeting: " + e.message, 'error');
        }
    };

    // Backwards compatibility for confirmMeeting
    window.confirmMeeting = window.approveMeetingEvent;

    // FEATURE 2: Reminder Actions
    window.openSnoozeModal = (reminderId) => {
        document.getElementById('snooze-reminder-id').value = reminderId;
        if (snoozeIntervalSelect) snoozeIntervalSelect.value = "15";
        if (customSnoozeGroup) customSnoozeGroup.style.display = "none";
        if (customSnoozeMinutes) customSnoozeMinutes.value = "";
        snoozeModal.style.display = 'flex';
    };

    window.handleReminder = async (reminderId) => {
        try {
            const res = await fetch(`/api/reminders/${reminderId}/handle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showToast("✓ Reminder marked as handled.", "success");
                await loadState();
            } else {
                showToast("Failed to mark reminder as handled: " + (data.error || "Unknown error"), "error");
            }
        } catch(e) {
            showToast("Error marking reminder handled: " + e.message, "error");
        }
    };

    window.replyNowReminder = (reminderId, emailId) => {
        // Find corresponding draft
        let draft = null;
        if (currentDrafts && currentDrafts.length > 0) {
            if (emailId) {
                draft = currentDrafts.find(d => d.id === emailId);
            }
            if (!draft) {
                draft = currentDrafts[0];
            }
        }

        if (draft) {
            openEditModal(draft.id, draft.subject, draft.body);
            showToast("Opening draft for review. Review and approve before sending.", "success");
        } else {
            showToast("No prepared draft found yet. Please click 'Process Inbox' first.", "error");
        }
    };
    
    function showToast(message, type = 'success') {
        const existing = document.getElementById('toast-notification');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.id = 'toast-notification';
        toast.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
            padding: 14px 20px;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 500;
            max-width: 440px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.1);
            color: #fff;
            background: ${ type === 'success'
                ? 'linear-gradient(135deg, rgba(16,185,129,0.95), rgba(5,150,105,0.95))'
                : 'linear-gradient(135deg, rgba(239,68,68,0.95), rgba(185,28,28,0.95))' };
            animation: slideInToast 0.3s ease;
        `;
        toast.textContent = message;

        if (!document.getElementById('toast-keyframes')) {
            const style = document.createElement('style');
            style.id = 'toast-keyframes';
            style.textContent = `
                @keyframes slideInToast {
                    from { transform: translateY(30px); opacity: 0; }
                    to   { transform: translateY(0);   opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }

    // Initial load
    loadState();

    // Auto-refresh state every 6 seconds to trigger due reminders and update diagnostics
    setInterval(loadState, 6000);
});
