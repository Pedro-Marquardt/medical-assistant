import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.infra.web.app:app", host="0.0.0.0", port=3030, reload=True)