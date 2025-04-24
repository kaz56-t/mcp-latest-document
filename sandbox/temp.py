from enum import Enum


class ToolURLS(Enum):
    # FrontEnd
    react = "https://react.dev/reference/react-dom"
    react_native = "https://reactnative.dev/docs/components-and-apis"
    chakra_ui = "https://chakra-ui.com/docs/components/concepts/overview"
    # Backend
    python = "https://docs.python.org/3/"
    go = "https://go.dev/doc/"

print(ToolURLS['python'].value)
print('te' in ToolURLS.__members__)