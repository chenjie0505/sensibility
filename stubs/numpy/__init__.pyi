from typing import Any, Iterable, NewType, Sequence, Sized, Tuple, TypeVar, Union
T = TypeVar('T')

DataType = NewType('DataType', int)
Shape = Union[int, Sequence[int]]

bool = ...  # type: DataType
float32 = ...  # type: DataType
float64 = ...  # type: DataType

class ndarray(Sized, Iterable[T]):
    def __setitem__(self, *i: Any) -> None: ...
    def __getitem__(self, *i: Any) -> T: ...
    def __matmul__(self, other: ndarray) -> Union[ndarray[T], T]: ...
    def __add__(self, other: ndarray[T]) -> ndarray[T]: ...
    def __sub__(self, other: ndarray[T]) -> ndarray[T]: ...

def array(object: Sequence, dtype: DataType=None) -> ndarray[T]: ...
def resize(a: ndarray[T], shape: Shape) -> ndarray[T]: ...
def zeros(shape: Shape,  dtype: DataType=None) -> ndarray[T]: ...
