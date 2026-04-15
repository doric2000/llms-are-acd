import inspect
import warnings

warnings.filterwarnings(
    "ignore",
    message="Gym has been unmaintained since 2022 and does not support NumPy 2.0 amongst other critical functionality.*",
    category=UserWarning,
)
# allows import of CybORG class as:
# from CybORG import CybORG
from CybORG.env import CybORG

path = str(inspect.getfile(CybORG))
path = path[:-7] + '/version.txt'
with open(path) as f:
    CYBORG_VERSION = f.read()[:-1]
