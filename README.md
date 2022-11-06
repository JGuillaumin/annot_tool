# Set local env with `conda`

```shell
conda create --name annot_tool python=3.10 -y

conda activate annot_tool
pip install -r requirements.txt -r requirements-dev.txt
```



# Setup pre-commit hooks 

```shell
pre-commit install
```


