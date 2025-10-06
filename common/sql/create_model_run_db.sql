CREATE TABLE IF NOT EXISTS model_runs (
    run_id UUID DEFAULT generateUUIDv4(),
    trained_at DateTime DEFAULT now(),
    model_name String,
    model_description String,
    s3_key String,
    retrain_interval Float64,
    train_accuracy Float64,
    test_accuracy Float64,
    precision Float64,
    recall Float64,
    f1 Float64               
    ) 
ENGINE = MergeTree()
ORDER BY (trained_at)