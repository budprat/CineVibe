gcloud authlist
gcloud auth list
gcloud config set account `p.budhwar@gmail.com`
gcloud config set account p.budhwar@gmail.com
gcloud auth list
git clone -b adk-1.2.1-a2a-0.2.7 https://github.com/weimeilin79/instavibe-bootstrap.git
chmod +x ~/instavibe-bootstrap/init.sh
chmod +x ~/instavibe-bootstrap/set_env.sh
cd ~/instavibe-bootstrap
./init.sh
gcloud config set project $(cat ~/project_id.txt) --quiet
gcloud services enable  run.googleapis.com                         cloudfunctions.googleapis.com                         cloudbuild.googleapis.com                         artifactregistry.googleapis.com                         spanner.googleapis.com                         apikeys.googleapis.com                         iam.googleapis.com                         compute.googleapis.com                         aiplatform.googleapis.com                         cloudresourcemanager.googleapis.com                         maps-backend.googleapis.com
export PROJECT_ID=$(gcloud config get project)
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
export SERVICE_ACCOUNT_NAME=$(gcloud compute project-info describe --format="value(defaultServiceAccount)")
export SPANNER_INSTANCE_ID="instavibe-graph-instance"
export SPANNER_DATABASE_ID="graphdb"
export GOOGLE_CLOUD_PROJECT=$(gcloud config get project)
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_LOCATION="us-central1"
gcloud services enable  run.googleapis.com                         cloudfunctions.googleapis.com                         cloudbuild.googleapis.com                         artifactregistry.googleapis.com                         spanner.googleapis.com                         apikeys.googleapis.com                         iam.googleapis.com                         compute.googleapis.com                         aiplatform.googleapis.com                         cloudresourcemanager.googleapis.com                         maps-backend.googleapis.com
gcloud services enable  run.googleapis.com                         cloudfunctions.googleapis.com                         cloudbuild.googleapis.com                         artifactregistry.googleapis.com                         spanner.googleapis.com                         apikeys.googleapis.com                         iam.googleapis.com                         compute.googleapis.com                         aiplatform.googleapis.com                         cloudresourcemanager.googleapis.com                         maps-backend.googleapis.com
gcloud services enable  run.googleapis.com                         cloudfunctions.googleapis.com                         cloudbuild.googleapis.com                         artifactregistry.googleapis.com                         spanner.googleapis.com                         apikeys.googleapis.com                         iam.googleapis.com                         compute.googleapis.com                         aiplatform.googleapis.com                         cloudresourcemanager.googleapis.com                         maps-backend.googleapis.com
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/spanner.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/spanner.databaseUser"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/artifactregistry.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/cloudbuild.builds.editor"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/cloudbuild.builds.editor"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/logging.logWriter"
gcloud projects add-iam-policy-binding $PROJECT_ID   --member="serviceAccount:$SERVICE_ACCOUNT_NAME"   --role="roles/logging.viewer"
export REPO_NAME="introveally-repo"
gcloud artifacts repositories create $REPO_NAME   --repository-format=docker   --location=us-central1   --description="Docker repository for InstaVibe workshop"
. ~/instavibe-bootstrap/set_env.sh
gcloud spanner instances create $SPANNER_INSTANCE_ID   --config=regional-us-central1   --description="GraphDB Instance InstaVibe"   --processing-units=100   --edition=ENTERPRISE
gcloud spanner databases create $SPANNER_DATABASE_ID   --instance=$SPANNER_INSTANCE_ID   --database-dialect=GOOGLE_STANDARD_SQL
echo "Granting Spanner read/write access to ${SERVICE_ACCOUNT_NAME} for database ${SPANNER_DATABASE_ID}..."
gcloud spanner databases add-iam-policy-binding ${SPANNER_DATABASE_ID}   --instance=${SPANNER_INSTANCE_ID}   --member="serviceAccount:${SERVICE_ACCOUNT_NAME}"   --role="roles/spanner.databaseUser"   --project=${PROJECT_ID}
. ~/instavibe-bootstrap/set_env.sh
cd ~/instavibe-bootstrap
python -m venv env
source env/bin/activate
pip install -r requirements.txt
cd instavibe
python setup.py
. ~/instavibe-bootstrap/set_env.sh
export KEY_DISPLAY_NAME="Maps Platform API Key"
GOOGLE_MAPS_KEY_ID=$(gcloud services api-keys list \
  --project="${PROJECT_ID}" \
  --filter="displayName='${KEY_DISPLAY_NAME}'" \
  --format="value(uid)" \
  --limit=1)
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
echo ${GOOGLE_MAPS_KEY_ID}
export GOOGLE_MAPS_KEY_ID="your-google-maps-key-id-here"
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
export KEY_DISPLAY_NAME="Maps Platform API Key"
GOOGLE_MAPS_KEY_ID=$(gcloud services api-keys list \
  --project="${PROJECT_ID}" \
  --filter="displayName='${KEY_DISPLAY_NAME}'" \
  --format="value(uid)" \
  --limit=1)
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
. ~/instavibe-bootstrap/set_env.sh
export KEY_DISPLAY_NAME="Maps Platform API Key"
GOOGLE_MAPS_KEY_ID=$(gcloud services api-keys list \
  --project="${PROJECT_ID}" \
  --filter="displayName='${KEY_DISPLAY_NAME}'" \
  --format="value(uid)" \
  --limit=1)
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
echo ${GOOGLE_MAPS_KEY_ID}
export ${GOOGLE_MAPS_KEY_ID}=your-google-maps-api-key-here
export ${GOOGLE_MAPS_KEY_ID}="your-google-maps-api-key-here"
export GOOGLE_MAPS_KEY_ID="your-google-maps-key-id-here"
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
echo ${GOOGLE_MAPS_KEY_ID}
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
# Replace "your-key-id-goes-here" with your actual Key ID
gcloud services api-keys get-key-string "your-key-id-goes-here"     --project="${PROJECT_ID}"     --format="value(keyString)"
gcloud services api-keys list --project="${PROJECT_ID}"
export GOOGLE_MAPS_KEY_ID="8bc32eb7-71af-4eed-8679-588dd96b9eac"
export GOOGLE_MAPS_KEY_ID="60c14585-d6df-4d27-acb7-ea181e8272c5"
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
GOOGLE_MAPS_KEY_ID=$(gcloud services api-keys list \
  --project="${PROJECT_ID}" \
  --filter="displayName='${KEY_DISPLAY_NAME}'" \
  --format="value(uid)" \
  --limit=1)
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
export GOOGLE_MAPS_KEY_ID="60c14585-d6df-4d27-acb7-ea181e8272c5"
GOOGLE_MAPS_API_KEY=$(gcloud services api-keys get-key-string "${GOOGLE_MAPS_KEY_ID}" \
    --project="${PROJECT_ID}" \
    --format="value(keyString)")
echo "${GOOGLE_MAPS_API_KEY}" > ~/mapkey.txt
echo "Retrieved GOOGLE_MAPS_API_KEY: ${GOOGLE_MAPS_API_KEY}"
. ~/instavibe-bootstrap/set_env.sh
cd ~/instavibe-bootstrap/instavibe/
export IMAGE_TAG="latest"
export APP_FOLDER_NAME="instavibe"
export IMAGE_NAME="instavibe-webapp"
export IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
export SERVICE_NAME="instavibe"
gcloud builds submit .   --tag=${IMAGE_PATH}   --project=${PROJECT_ID}
. ~/instavibe-bootstrap/set_env.sh
cd ~/instavibe-bootstrap/instavibe/
export IMAGE_TAG="latest"
export APP_FOLDER_NAME="instavibe"
export IMAGE_NAME="instavibe-webapp"
export IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
export SERVICE_NAME="instavibe"
gcloud run deploy ${SERVICE_NAME}   --image=${IMAGE_PATH}   --platform=managed   --region=${REGION}   --allow-unauthenticated   --set-env-vars="SPANNER_INSTANCE_ID=${SPANNER_INSTANCE_ID}"   --set-env-vars="SPANNER_DATABASE_ID=${SPANNER_DATABASE_ID}"   --set-env-vars="APP_HOST=0.0.0.0"   --set-env-vars="APP_PORT=8080"   --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}"   --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"   --set-env-vars="GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}"   --project=${PROJECT_ID}   --min-instances=1
. ~/instavibe-bootstrap/set_env.sh
source ~/instavibe-bootstrap/env/bin/activate
cd  ~/instavibe-bootstrap/agents
sed -i "s|^\(O\?GOOGLE_CLOUD_PROJECT\)=.*|GOOGLE_CLOUD_PROJECT=${PROJECT_ID}|" ~/instavibe-bootstrap/agents/planner/.env
adk web
ls
npm install -g @anthropic-ai/claude-code
npm -v
node -v
echo "Deleting Spanner instance: ${SPANNER_INSTANCE_ID}..."
gcloud spanner instances delete ${SPANNER_INSTANCE_ID} --project=${PROJECT_ID} --quiet
. ~/instavibe-bootstrap/set_env.sh
gcloud spanner instances delete ${SPANNER_INSTANCE_ID} --project=${PROJECT_ID} --quiet
echo "Deleting Spanner instance: ${SPANNER_INSTANCE_ID}"
gcloud spanner backups delete BACKUP_NAME --instance=INSTANCE_ID
cd ~/instavibe-bootstrap/utils
source ~/instavibe-bootstrap/env/bin/activate
export ORCHESTRATE_AGENT_ID=$(cat ~/instavibe-bootstrap/instavibe/temp_endpoint.txt)
echo "ORCHESTRATE_AGENT_ID set to: ${ORCHESTRATE_AGENT_ID}"
python remote_delete.py
deactivate
gcloud run services delete instavibe --platform=managed --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete mcp-tool-server --platform=managed --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete planner-agent --platform=managed --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete platform-mcp-client --platform=managed --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete social-agent --platform=managed --region=${REGION} --project=${PROJECT_ID} --quiet
docker rm --force a2a-inspector
gcloud spanner instances delete ${SPANNER_INSTANCE_ID} --project=${PROJECT_ID} --quiet
gcloud artifacts repositories delete ${REPO_NAME} --location=${REGION} --project=${PROJECT_ID} --quiet
claude
history
npm install -g @anthropic-ai/claude-code
ls
claude
npm install -g @anthropic-ai/claude-code
claude
npm install -g @anthropic-ai/claude-code
gcloud spanner instances delete $SPANNER_INSTANCE_ID
claude --dangerously-skip-permissions
npm install -g @anthropic-ai/claude-code
