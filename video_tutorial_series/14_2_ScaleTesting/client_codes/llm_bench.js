import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { Counter } from 'k6/metrics';

// --- METRICS ---
const model1Hits = new Counter('hits_qwen_block');
const model2Hits = new Counter('hits_qwen_block_2');

export function setup() {
    const testId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        let r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });

    console.log(`\n🚀 BENCHMARK STARTED`);
    console.log(`GLOBAL_TEST_ID: ${testId}\n`);

    // This return value is passed to the default function as "data"
    return { testId: testId };
}


// --- CONFIGURATION ---
const INFERENCE_SERVERS = [
    "http://CLUSTER_2_MASTER_NODE:31504/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31604/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31704/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31806/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31904/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31913/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31918/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31933/v1/infer",
    "http://CLUSTER_2_MASTER_NODE:31938/v1/infer"
];

// Inference server metrics
const serverHitsCounters = {};
INFERENCE_SERVERS.forEach((server, idx) => {
    serverHitsCounters[server] = new Counter(`hits_server_${idx + 1}`);
});

const DMA_LOG_ENDPOINT = "http://CLUSTER_2_MASTER_NODE:12345/create_entry";
//const DMA_LOG_ENDPOINT = "http://2ND_DMA_ENDPOINT:12345/create_entry"; //second end point to handle more request


// --- BENCHMARK PARAMETERS ---
const TOTAL_SIMULATED_USERS = 40000;
const USERS_PER_MODEL = 10000; // Users split across 4 models (10k each)

const TARGET_RPS = 150;
export const options = {
    scenarios: {
        inference_load: {
            executor: 'constant-arrival-rate',
            rate: TARGET_RPS,
            timeUnit: '1s',
            duration: '1440m',
            maxVUs: TOTAL_SIMULATED_USERS,
            preAllocatedVUs: 500, // Pre-warm 500
        },
    },
};



export default function (data) {

    const currentTestId = data.testId;

    const iterationId = exec.scenario.iterationInTest;
    const simulatedUserId = (iterationId % TOTAL_SIMULATED_USERS) + 1;

    // 1. Logic for Model ID Split
    const models = [
        "qwen3-5-0-8b-vllm-block",
        "qwen3-5-0-8b-vllm-block-2"
    ];
    const modelId = models[iterationId % models.length];

    if (modelId === "qwen3-5-0-8b-vllm-block") model1Hits.add(1);
    else if (modelId === "qwen3-5-0-8b-vllm-block-2") model2Hits.add(1);

    // 2. Round Robin for Server URLs
    const url = INFERENCE_SERVERS[iterationId % INFERENCE_SERVERS.length];

    if (serverHitsCounters[url]) serverHitsCounters[url].add(1);

    const totalHits = iterationId + 1;
    if (totalHits % 5000 === 0) {
        console.log(`\n[PROGRESS] Total requests so far: ${totalHits}`);
        models.forEach((m, idx) => {
            const mCount = Math.floor(totalHits / models.length) + (totalHits % models.length > idx ? 1 : 0);
            console.log(`   -> Model ${m} hits: ${mCount}`);
        });
        INFERENCE_SERVERS.forEach((server, idx) => {
            const sCount = Math.floor(totalHits / INFERENCE_SERVERS.length) + (totalHits % INFERENCE_SERVERS.length > idx ? 1 : 0);
            console.log(`   -> Server ${server} hits: ${sCount}`);
        });
        console.log(`GLOBAL_TEST_ID: ${data.testId}\n`);
    }

    const sessionId = `sessk6-${simulatedUserId}`;
    const seqNo = iterationId;

    // 3. Prepare Qwen Payload
    const payload = JSON.stringify({
        "model": modelId,
        "session_id": sessionId,
        "seq_no": seqNo,
        "data": {
            "mode": "generate",
            "generation_config": {
                "max_tokens": 256,
                "top_k": 50,
                "top_p": 0.95,
                "min_p": 0.0,
                "temperature": 1.0
            },
            "prompt": "Given the increasing prevalence of data analysis in professional basketball, how might incorporating advanced metrics like Expected Possession Value (EPV) and player tracking data influence coaching decisions regarding offensive schemes, defensive strategies, and player rotations, and what potential limitations or biases could arise from over-reliance on these metrics?. /no_think",
            "system_message": "You are a helpful assistant."
        },
        "graph": {},
        "files": {},
        "selection_query": {},
        "timeout": 1200
    });

    const params = {
        headers: { 'Content-Type': 'application/json' },
        timeout: '1000s', // Increased for LLM inference
    };

    // 4. Execute Main Request
    const startTime = new Date();
    let response = { status: 0, error: 'Exception', body: '' };
    let endTime;

    try {
        response = http.post(url, payload, params);
        endTime = new Date();
    } catch (e) {
        endTime = new Date();
        console.log(`❌ Exception caught during http.post! Error: ${e.message || e} | URL: ${url}`);
        response.error = e.message || e;
    }

    if (response.status !== 200) {
        console.log(`❌ Request Failed! Status: ${response.status} | URL: ${url} | Error: ${response.error}`);
        // This will print the actual body (e.g., "Connection Refused" or "Gateway Timeout")
        console.log(`Response Body: ${response.body}`);
    }
    const responseTimeSec = (endTime - startTime) / 1000;

    // 5. Log to DMA (Following your Python dict structure)
    const dataDumpToDMA = JSON.stringify({
        "block_id": modelId,
        "session_id": sessionId,
        "seq_no": seqNo,
        "type": response.status === 200 ? "success" : "failure",
        "response_time": responseTimeSec,
        "raw": "{}", // Keeping it light as per your code
        "test_id": currentTestId,
        "user_id": `userk6-${simulatedUserId}`,
        "starttime": startTime.getTime() / 1000,
        "endtime": endTime.getTime() / 1000,
        "starttimeObj": startTime.toISOString(),
        "endtimeObj": endTime.toISOString()
    });

    // 5. Log to DMA with retry (up to 3 attempts)
    if (DMA_LOG_ENDPOINT) {
        let logSuccess = false;
        let logAttempts = 0;
        const maxLogAttempts = 3;

        while (!logSuccess && logAttempts < maxLogAttempts) {
            logAttempts++;
            const logResponse = http.post(DMA_LOG_ENDPOINT, dataDumpToDMA, {
                headers: { 'Content-Type': 'application/json' },
                timeout: '5s', // Slightly increased timeout for logging
            });

            if (logResponse.status === 200 || logResponse.status === 201) {
                logSuccess = true;
            } else {
                console.log(`⚠️ DMA Log Failed (Attempt ${logAttempts}/${maxLogAttempts}): Status ${logResponse.status}, Error: ${logResponse.error || 'Unknown'}`);
                if (logAttempts < maxLogAttempts) {
                    console.log(`Retrying in 2s...`);
                    sleep(2);
                } else {
                    console.log(`❌ Max retries reached for DMA log. Data for this iteration may be lost.`);
                }
            }
        }
    }

    // 6. Metrics Check
    check(response, {
        'status is 200': (r) => r.status === 200,
    });
}

export function teardown(data) {
    console.log(`\n✅ BENCHMARK FINISHED`);
    console.log(`GLOBAL_TEST_ID: ${data.testId}\n`);
}
