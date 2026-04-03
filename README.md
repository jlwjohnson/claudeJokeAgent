# Claude Joke Agent

A Claude AI agent that tells jokes by category (dad, animal, kid), built with Python/FastAPI and Claude on AWS Bedrock. Designed to be called from a Camunda 8 BPMN process via the REST connector.

## What's in the box

| File | Purpose |
|------|---------|
| `app.py` | Python REST API that calls Claude on AWS Bedrock to generate jokes |
| `joke-agent-process.bpmn` | Camunda 8 BPMN process with a REST connector service task |
| `requirements.txt` | Python dependencies |

## Prerequisites

- **Python 3.9+** (check with `python3 --version`)
- **An AWS account** with access to Amazon Bedrock
- **A Camunda 8 SaaS account** (free trial works) — only needed for the BPMN integration
- **ngrok account** (free) — needed to expose your local agent to Camunda SaaS

---

## Step 1: AWS Setup

### 1a. Create an AWS IAM User

1. Go to the [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click **Users** > **Create user**
3. Give it a name (e.g., `bedrock-joke-agent`)
4. Click **Next**, then **Attach policies directly**
5. Search for and attach: `AmazonBedrockFullAccess`
   - (Or for tighter permissions, create a custom policy with just `bedrock:InvokeModel`)
6. Click **Next** > **Create user**
7. Click the user name > **Security credentials** tab > **Create access key**
8. Choose **Command Line Interface (CLI)**, confirm, and click **Create access key**
9. **Save both values** — you'll need them below:
   - Access key ID (e.g., `AKIA...`)
   - Secret access key (e.g., `wJalr...`)

### 1b. Enable Claude in Amazon Bedrock

1. Go to [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Make sure you're in **us-east-1** (N. Virginia) region
3. In the left sidebar, click **Model access**
4. Click **Modify model access**
5. Find **Anthropic** and check **Claude Haiku**
6. Click **Next** > **Submit**
7. Wait for status to show "Access granted" (usually seconds, sometimes a few minutes)

### 1c. Configure AWS Credentials Locally

Create the file `~/.aws/credentials`:

```
[default]
aws_access_key_id=YOUR_ACCESS_KEY_ID
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
```

Create the file `~/.aws/config`:

```
[default]
region=us-east-1
```

**Important:** Both files must have the `[default]` header or boto3 will fail to parse them.

Alternatively, set environment variables instead:

```bash
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
export AWS_REGION=us-east-1
```

---

## Step 2: Install and Run the Joke Agent

### 2a. Clone and Install

```bash
git clone https://github.com/jlwjohnson/camunda-video-demos.git
cd camunda-video-demos
pip install -r requirements.txt
```

> **Note:** If `pip` installs to a path not on your system PATH, use `python3 -m pip install -r requirements.txt` instead.

### 2b. Start the Server

```bash
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2c. Test Locally

Open a new terminal and run:

```bash
# GET request (simplest)
curl "http://localhost:8000/joke?joke_type=dad"

# POST request
curl -X POST http://localhost:8000/joke \
  -H "Content-Type: application/json" \
  -d '{"joke_type": "animal"}'
```

You should get a response like:

```json
{
  "joke_type": "dad",
  "joke": "Why don't scientists trust atoms?\n\nBecause they make up everything!"
}
```

Supported joke types: `dad`, `animal`, `kid`

---

## Step 3: Expose with ngrok (Required for Camunda SaaS)

Camunda 8 SaaS runs in the cloud and can't reach `localhost` on your machine. ngrok creates a public tunnel to your local server.

### 3a. Create an ngrok Account

1. Go to [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup)
2. Sign up for a free account
3. Go to [https://dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
4. Copy your authtoken

### 3b. Install ngrok

**macOS (Homebrew):**

```bash
brew install ngrok
```

**macOS (manual download):**

```bash
curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-arm64.zip -o /tmp/ngrok.zip
unzip -o /tmp/ngrok.zip -d /usr/local/bin/
```

**Other platforms:** Download from [https://ngrok.com/download](https://ngrok.com/download)

### 3c. Configure ngrok

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

### 3d. Start the Tunnel

Make sure the joke agent server is running (Step 2b), then in a **new terminal**:

```bash
ngrok http 8000
```

You'll see output like:

```
Forwarding  https://abc123.ngrok-free.dev -> http://localhost:8000
```

**Copy the `https://...ngrok-free.dev` URL** — this is your public endpoint.

Test it:

```bash
curl "https://abc123.ngrok-free.dev/joke?joke_type=kid" \
  -H "ngrok-skip-browser-warning: true"
```

> **Important:** Both the joke agent server AND ngrok must be running at the same time. If either one stops, the public URL will go offline.

---

## Step 4: Camunda 8 Integration

### 4a. Configure the REST Connector

1. Open `joke-agent-process.bpmn` in Camunda Web Modeler
2. Click the **Call Claude Joke Agent** service task
3. Configure the REST connector:

| Field | Value |
|-------|-------|
| **Authentication** | `None` |
| **Method** | `GET` |
| **URL** | `https://YOUR-NGROK-URL.ngrok-free.dev/joke` |
| **Headers** | `={"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}` |
| **Query Parameters** | `={"joke_type": jokeType}` |

4. Set the **Result Expression** to:

```
={"joke": response.body}
```

### 4b. Deploy and Run

1. Deploy the process to your Camunda 8 SaaS cluster
2. Start a new process instance with the variable:

```json
{
  "jokeType": "dad"
}
```

3. Check the completed instance in Operate — the `joke` variable will contain the joke

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ConfigParseError: Unable to parse config file` | Make sure `~/.aws/credentials` and `~/.aws/config` both have the `[default]` header line |
| `command not found: uvicorn` | Use `python3 -m uvicorn` instead of `uvicorn` |
| `No module named uvicorn` | Run `pip install -r requirements.txt` (or `python3 -m pip install -r requirements.txt`) |
| ngrok `ERR_NGROK_4018` | You need to sign up and configure your authtoken (see Step 3) |
| ngrok `ERR_NGROK_3200` (endpoint offline) | Restart both the joke agent server and ngrok |
| `AccessDeniedException` from Bedrock | Enable Claude Haiku in Bedrock model access (see Step 1b) |
| Camunda `response.body.joke` error | Use `={"joke": response.body}` as the result expression — the response body is a string, not JSON |

---

## API Reference

### GET /joke

Returns a joke of the specified type.

```
GET /joke?joke_type=dad
```

**Query Parameters:**
- `joke_type` (string): One of `dad`, `animal`, `kid`. Defaults to `dad`.

**Response:**

```json
{
  "joke_type": "dad",
  "joke": "Why don't scientists trust atoms?\n\nBecause they make up everything!"
}
```

### POST /joke

Same as GET but accepts a JSON body.

```
POST /joke
Content-Type: application/json

{"joke_type": "animal"}
```

### GET /health

Health check endpoint.

```
GET /health
```

**Response:** `{"status": "ok"}`
