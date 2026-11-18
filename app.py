import os
import json
import csv
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
AGENTS_FILE = os.path.join(BASE_DIR, 'agents.json')
AUDIT_LOG_FILE = os.path.join(BASE_DIR, 'audit_log.csv')
ENROLLMENT_NUMBER = "PGD202564690"

# Ensure agents.json exists with preloaded agents
if not os.path.exists(AGENTS_FILE):
    initial_agents = [
        {
            "agent_name": "TravelBot",
            "customer_name": "Vishal",
            "status": "active",
            "registered_at": datetime.now().isoformat(),
            "revoked_at": ""
        },
        {
            "agent_name": "SkyAssistant",
            "customer_name": "Rahul",
            "status": "active",
            "registered_at": datetime.now().isoformat(),
            "revoked_at": ""
        }
    ]
    with open(AGENTS_FILE, 'w') as f:
        json.dump(initial_agents, f, indent=2)

# Ensure audit_log.csv exists with header
if not os.path.exists(AUDIT_LOG_FILE):
    with open(AUDIT_LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "customer", "agent_name", "action", "amount", "decision", "rule_triggered"])

def load_agents():
    with open(AGENTS_FILE, 'r') as f:
        return json.load(f)

def save_agents(agents):
    with open(AGENTS_FILE, 'w') as f:
        json.dump(agents, f, indent=2)

def log_audit(entry):
    with open(AUDIT_LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(entry)

def evaluate_rules(customer, agent_name, action, amount):
    agents = load_agents()
    # Rule 1: Unknown Agent
    agent = next((a for a in agents if a["agent_name"].lower() == agent_name.lower()), None)
    if not agent:
        return "BLOCK", "Rule 1: Unknown Agent"
    # Rule 2: Revoked Agent
    if agent["status"].lower() == "revoked":
        return "BLOCK", "Rule 2: Revoked Agent"
    # Rule 3: Read‑Only Action
    if action == "view fares":
        return "ALLOW", "Rule 3: Read‑Only Action"
    # Rule 4 & 5: Booking limits
    if action == "book":
        if amount <= 15000:
            return "ALLOW", "Rule 4: Booking within ₹15,000 limit"
        else:
            return "ASK CUSTOMER", "Rule 5: Booking exceeds ₹15,000 limit"
    # Rule 6: Change limits
    if action == "change":
        if amount <= 5000:
            return "ALLOW", "Rule 6: Flight Change Policy (within limit)"
        else:
            return "ASK CUSTOMER", "Rule 6: Flight Change Policy (exceeds limit)"
    # Rule 7: Refund always asks
    if action == "refund":
        return "ASK CUSTOMER", "Rule 7: Refund requires customer confirmation"
    # Default fallback
    return "BLOCK", "Rule 0: No matching rule"

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IndiGo Agent Gatekeeper</title>
<style>
  body {font-family: Arial, sans-serif; margin: 20px; background:#f9f9f9;}
  h1 {color:#333;}
  .section {background:#fff; padding:15px; margin-bottom:20px; border-radius:5px; box-shadow:0 2px 4px rgba(0,0,0,0.1);}
  label {display:block; margin-top:8px;}
  input, select {width:100%; padding:6px; margin-top:4px;}
  button {margin-top:12px; padding:8px 12px;}
  .decision {font-weight:bold; padding:8px; margin-top:10px; display:inline-block;}
  .allow {color:#155724; background:#d4edda;}
  .ask {color:#856404; background:#fff3cd;}
  .block {color:#721c24; background:#f8d7da;}
  table {width:100%; border-collapse:collapse; margin-top:10px;}
  th, td {border:1px solid #ddd; padding:8px; text-align:left;}
  th {background:#f2f2f2;}
</style>
</head>
<body>
<h1>IndiGo Agent Gatekeeper</h1>
<p><strong>Enrolment Number:</strong> {{ enrolment }}</p>

<div class="section">
  <h2>1. Test Agent Request</h2>
  <form method="post" action="{{ url_for('index') }}">
    <input type="hidden" name="form_type" value="test_request">
    <label>Customer Name:
      <input type="text" name="customer" required>
    </label>
    <label>Agent Name:
      <input type="text" name="agent_name" required>
    </label>
    <label>Action:
      <select name="action" required>
        <option value="view fares">view fares</option>
        <option value="book">book</option>
        <option value="change">change</option>
        <option value="refund">refund</option>
      </select>
    </label>
    <label>Amount (INR):
      <input type="number" name="amount" min="0" step="1" required>
    </label>
    <button type="submit">Submit Request</button>
  </form>
  {% if decision %}
    <div class="decision {{ decision_class }}">{{ decision }} – {{ rule }}</div>
  {% endif %}
</div>

<div class="section">
  <h2>2. Manage Agents</h2>
  <form method="post" action="{{ url_for('index') }}">
    <input type="hidden" name="form_type" value="add_agent">
    <label>Agent Name:
      <input type="text" name="new_agent_name" required>
    </label>
    <label>Customer Name:
      <input type="text" name="new_customer_name" required>
    </label>
    <button type="submit">Register Agent</button>
  </form>
  <h3>Current Agents</h3>
  <table>
    <tr><th>Agent Name</th><th>Customer</th><th>Status</th><th>Registered At</th><th>Revoked At</th><th>Action</th></tr>
    {% for a in agents %}
    <tr>
      <td>{{ a.agent_name }}</td>
      <td>{{ a.customer_name }}</td>
      <td>{{ a.status }}</td>
      <td>{{ a.registered_at }}</td>
      <td>{{ a.revoked_at }}</td>
      <td>
        {% if a.status != 'revoked' %}
          <form method="post" style="display:inline;" action="{{ url_for('revoke', agent_name=a.agent_name) }}">
            <button type="submit">Revoke</button>
          </form>
        {% else %}
          —
        {% endif %}
      </td>
    </tr>
    {% endfor %}
  </table>
</div>

<div class="section">
  <h2>3. Live Audit Log</h2>
  <table>
    <tr><th>Timestamp</th><th>Customer</th><th>Agent</th><th>Action</th><th>Amount</th><th>Decision</th><th>Rule</th></tr>
    {% for row in audit %}
    <tr>
      <td>{{ row.timestamp }}</td>
      <td>{{ row.customer }}</td>
      <td>{{ row.agent_name }}</td>
      <td>{{ row.action }}</td>
      <td>{{ row.amount }}</td>
      <td>{{ row.decision }}</td>
      <td>{{ row.rule_triggered }}</td>
    </tr>
    {% endfor %}
  </table>
</div>

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    decision = None
    rule = None
    decision_class = None
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'test_request':
            customer = request.form['customer']
            agent_name = request.form['agent_name']
            action = request.form['action']
            amount = float(request.form['amount'])
            decision, rule = evaluate_rules(customer, agent_name, action, amount)
            # log the request
            log_audit([
                datetime.now().isoformat(),
                customer,
                agent_name,
                action,
                amount,
                decision,
                rule
            ])
            # set CSS class based on decision
            if decision == "ALLOW":
                decision_class = "allow"
            elif decision == "ASK CUSTOMER":
                decision_class = "ask"
            else:
                decision_class = "block"
        elif form_type == 'add_agent':
            new_agent = request.form['new_agent_name']
            new_customer = request.form['new_customer_name']
            agents = load_agents()
            agents.append({
                "agent_name": new_agent,
                "customer_name": new_customer,
                "status": "active",
                "registered_at": datetime.now().isoformat(),
                "revoked_at": ""
            })
            save_agents(agents)
            return redirect(url_for('index'))
    # Load data for display
    agents = load_agents()
    # Load audit log
    audit = []
    with open(AUDIT_LOG_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            audit.append(row)
    return render_template_string(
        HTML_TEMPLATE,
        enrolment=ENROLLMENT_NUMBER,
        decision=decision,
        rule=rule,
        decision_class=decision_class,
        agents=agents,
        audit=audit
    )

@app.route('/revoke/<agent_name>', methods=['POST'])
def revoke(agent_name):
    agents = load_agents()
    for a in agents:
        if a["agent_name"].lower() == agent_name.lower():
            a["status"] = "revoked"
            a["revoked_at"] = datetime.now().isoformat()
            break
    save_agents(agents)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
