# Architecture Diagram

## Runtime Architecture

```mermaid
flowchart LR
    ops["Railway Operations Users"]
    supervisor["Supervisors / Admins"]
    idp["SSO / JWT Identity Provider"]
    gemini["Google Gemini API"]
    redis["Redis State Store\n(optional in prod)"]
    audit["Hash-Chained Audit Log"]
    history["Historical Incident Dataset\nCSV / XLSX"]
    metrics["Prometheus / OTEL"]

    subgraph edge["Edge / Access Layer"]
        ingress["Ingress / Trusted Host / CORS / WAF / mTLS"]
    end

    subgraph api["FastAPI Application"]
        routes["API Routes\n/chat/*\n/incident/classify\n/feedback\n/metrics"]
        security["Security Controls\nJWT or Stub SSO\nRate Limiter\nDDoS Guard\nIP Reputation\nPrompt Injection Guard"]

        subgraph orchestration["Assistant Orchestrator"]
            intake["Intake Agent"]
            questioning["Questioning Agent"]
            classification["Classification Agent"]
            retrieval["Retrieval Agent"]
            recommendation["Recommendation Agent"]
            safety["Safety Agent"]
        end
    end

    ops --> ingress
    supervisor --> ingress
    ingress --> routes
    routes --> security
    security --> idp
    routes --> intake
    intake --> questioning
    questioning --> classification
    classification --> gemini
    classification --> redis
    classification --> retrieval
    retrieval --> history
    retrieval --> recommendation
    classification --> recommendation
    recommendation --> safety
    safety --> routes
    routes --> audit
    routes --> metrics
    security --> redis
    routes --> redis

    classDef external fill:#f6f3ea,stroke:#7a6a3a,color:#1f1a12
    classDef platform fill:#e8f1f8,stroke:#3f6b8a,color:#10202d
    classDef agent fill:#eef7ee,stroke:#4e7c59,color:#142417
    class ops,supervisor,idp,gemini,redis,audit,history,metrics external
    class ingress,routes,security platform
    class intake,questioning,classification,retrieval,recommendation,safety agent
```

## Production Deployment View

```mermaid
flowchart TB
    users["Users"]
    subgraph k8s["Kubernetes Cluster"]
        ingress["NGINX Ingress\nRate Limits + ModSecurity + mTLS"]
        service["ClusterIP Service"]
        subgraph pods["RIA Deployment\n3 replicas"]
            pod1["FastAPI Pod"]
            pod2["FastAPI Pod"]
            pod3["FastAPI Pod"]
        end
        otel["OTEL Collector"]
        redis["Redis"]
    end
    gemini["Google Gemini API"]
    idp["Identity Provider / JWKS"]

    users --> ingress
    ingress --> service
    service --> pod1
    service --> pod2
    service --> pod3
    pod1 --> redis
    pod2 --> redis
    pod3 --> redis
    pod1 --> gemini
    pod2 --> gemini
    pod3 --> gemini
    pod1 --> idp
    pod2 --> idp
    pod3 --> idp
    pod1 --> otel
    pod2 --> otel
    pod3 --> otel
```

## Notes

- The app can run with in-memory state locally, but production manifests point to Redis.
- Classification is the only agent step that depends on Gemini; retrieval and policy evaluation remain local.
- Audit logging is append-only and hash-chained to support integrity verification.
