# Copyright (c), Edoardo Tenani <e.tenani@arduino.cc>, 2018-2020
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils._text import to_text, to_native

from subprocess import Popen, PIPE


# From https://github.com/mozilla/sops/blob/master/cmd/sops/codes/codes.go
# Should be manually updated
SOPS_ERROR_CODES = {
    1: "ErrorGeneric",
    2: "CouldNotReadInputFile",
    3: "CouldNotWriteOutputFile",
    4: "ErrorDumpingTree",
    5: "ErrorReadingConfig",
    6: "ErrorInvalidKMSEncryptionContextFormat",
    7: "ErrorInvalidSetFormat",
    8: "ErrorConflictingParameters",
    21: "ErrorEncryptingMac",
    23: "ErrorEncryptingTree",
    24: "ErrorDecryptingMac",
    25: "ErrorDecryptingTree",
    49: "CannotChangeKeysFromNonExistentFile",
    51: "MacMismatch",
    52: "MacNotFound",
    61: "ConfigFileNotFound",
    85: "KeyboardInterrupt",
    91: "InvalidTreePathFormat",
    100: "NoFileSpecified",
    128: "CouldNotRetrieveKey",
    111: "NoEncryptionKeyFound",
    200: "FileHasNotBeenModified",
    201: "NoEditorFound",
    202: "FailedToCompareVersions",
    203: "FileAlreadyEncrypted"
}


class SopsError(Exception):
    ''' Extend Exception class with sops specific informations '''

    def __init__(self, filename, exit_code, message, decryption=True):
        if exit_code in SOPS_ERROR_CODES:
            exception_name = SOPS_ERROR_CODES[exit_code]
            message = "error with file %s: %s exited with code %d: %s" % (
                filename, exception_name, exit_code, to_native(message))
        else:
            message = "could not %s file %s; Unknown sops error code: %s; message: %s" % (
                'decrypt' if decryption else 'encrypt', filename, exit_code, to_native(message))
        super(SopsError, self).__init__(message)


class Sops():
    ''' Utility class to perform sops CLI actions '''

    @staticmethod
    def decrypt(encrypted_file, display=None, decode_output=True, rstrip=True, input_type=None, output_type=None):
        # Run sops directly, python module is deprecated
        command = ["sops"]
        if input_type is not None:
            command.extend(["--input-type", input_type])
        if output_type is not None:
            command.extend(["--output-type", output_type])
        command.extend(["--decrypt", encrypted_file])
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        (output, err) = process.communicate()
        exit_code = process.returncode

        if decode_output:
            # output is binary, we want UTF-8 string
            output = to_text(output, errors='surrogate_or_strict')
            # the process output is the decrypted secret; be cautious

        # sops logs always to stderr, as stdout is used for
        # file content
        if err and display:
            display.vvvv(to_text(err, errors='surrogate_or_strict'))

        if exit_code > 0:
            raise SopsError(encrypted_file, exit_code, err, decryption=True)

        if rstrip:
            output = output.rstrip()

        return output

    @staticmethod
    def encrypt(data, display=None, cwd=None, input_type=None, output_type=None):
        # Run sops directly, python module is deprecated
        command = ["sops"]
        if input_type is not None:
            command.extend(["--input-type", input_type])
        if output_type is not None:
            command.extend(["--output-type", output_type])
        command.extend(["--encrypt", "/dev/stdin"])
        process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=cwd)
        (output, err) = process.communicate(input=data)
        exit_code = process.returncode

        # sops logs always to stderr, as stdout is used for
        # file content
        if err and display:
            display.vvvv(to_text(err, errors='surrogate_or_strict'))

        if exit_code > 0:
            raise SopsError('to stdout', exit_code, err, decryption=False)

        return output
