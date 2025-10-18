#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_point import SourcePoint


def run():
    source = SourcePoint()
    launch(source, sys.argv[1:])


if __name__ == "__main__":
    run()