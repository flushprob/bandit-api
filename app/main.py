import os

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Response,
    status,
    Request,
    Depends,
    BackgroundTasks,
)
from dependency_injector.wiring import inject, Provide

from app.algorithms.egreedy import EGreedy
from app.algorithms.linucb import LinUCB
from app.containers import Container
from app.models.pymodels import BanditCreateModelRequest, BanditSelectActionRequest, GeneralResponse

dirpath = os.path.dirname(os.path.abspath(__file__))

load_dotenv(f"{dirpath}/env/{os.environ.get('ENV', 'local')}/.env")


app = FastAPI(
    title="Bandit API",
    description="Bandit API",
    version="0.0.1",
    contact={
        "name": "Chris Hoyean Song",
        "email": "sjhshy@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


@app.post("/v1/models/create", status_code=status.HTTP_201_CREATED)
async def v1_models_create_model(
    request: BanditCreateModelRequest,
    egreedy: EGreedy = Depends(Provide[Container.egreedy]),
    linucb: LinUCB = Depends(Provide[Container.linucb]),
):
    """
    Create a model
    """
    if request.algorithm == "egreedy":
        await egreedy.create_model(request.model_name, request.actions, request.epsilon)
    elif request.algorithm == "linucb":
        await linucb.create_model(request.model_name, request.actions, request.n_features, request.alpha)

    return GeneralResponse(message="OK", status_code=status.HTTP_201_CREATED, data={})


@app.post("/v1/bandit/select-action", status_code=status.HTTP_200_OK)
async def v1_bandit_select_action(
        request: BanditSelectActionRequest,
        response: Response,
):
    try:
        if request.model_name == "baseline" and request.model_version == "1":
            data = baseline_v1(request)
        elif request.model_name == "estimate-ratio" and request.model_version == "1":
            data = estimate_ratio_v1(request)
        data, message = service.insert_strategy(request, data)

        return GeneralResponse(status_code=20000, message=message, data=data).dict(by_alias=True)
    except Exception as e:
        message = f"{e}\n{traceback.format_exc()}"
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return GeneralResponse(status_code=50000, message=f"Exception: {e}", data={}).dict(by_alias=True)


container = Container()
container.config.redis_host.from_env("REDIS_HOST", "localhost")
container.config.redis_port.from_env("REDIS_PORT", "6379")
container.config.redis_db.from_env("REDIS_DB", "0")
container.wire(modules=[
    __name__,
])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
