#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Junior Polegato
# Date..: 22 May 2013
# About.: A converter from GSM/PDU to Unicode/UTF-8, and vice-versa

# http://www.developershome.com/sms/gsmAlphabet.asp
gsm_7_bit_chars = (u'@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1BÆæßÉ' #  0 -  31
                   u' !"#¤%&\'()*+,-./0123456789:;<=>?'     # 32 -  63
                   u'¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§'      # 64 -  95
                   u'¿abcdefghijklmnopqrstuvwxyzäöñüà'      # 96 - 127
                   u'\f^{}\\[~]|€')                         # Escaped
# Escaped characters gsm codes
gsm_esc_seq = (10, 20, 40, 41, 47, 60, 61, 62, 64, 101)

# Convert a utf-8 or unicode text into gsm code sequence
def text_to_gsm_code(text):
    # If text not in unicode, convert/decode to unicode
    if not isinstance(text, unicode):
        text = str(text).decode('utf-8')
    # gsm code list
    gsm = []
    # For each character in text
    for c in text:
        # If character in GSM table return de code, else return a dot
        if c in gsm_7_bit_chars:
            i = gsm_7_bit_chars.index(c)
            # If the GSM code is greater then 127, escape the code
            if i > 127:
                gsm.append(27) # ESC
                gsm.append(gsm_esc_seq[i - 128])
            else:
                gsm.append(i)
        else:
            gsm.append(46) # '.'
    return gsm

# Convert a gsm code sequence into a unicode text 
def gsm_code_to_text(gsm):
    # If de gsm code is in string, convert to list of integers
    if isinstance(gsm, (str, unicode)):
        gsm = [ord(g) for f in gsm]
    # The text converted
    text = u''
    escaped = False
    # For each code in gsm code list
    for c in gsm:
        # If the code between 0 and 127, process, else add a dot
        if -1 < c < 128:
            # If escaped, put the character escaped, else ESC + char
            if escaped:
                escaped = False
                if c in gsm_esc_seq:
                    text += gsm_7_bit_chars[128 + gsm_esc_seq.index(c)]
                else:
                    text += '\x1B' + gsm_7_bit_chars[c]
            # If not escaped and c is ESC, then continue in escaped mode
            elif c == 27:
                escaped = True
            # Else, add a unicode character respective to gsm code 
            else:
                text += gsm_7_bit_chars[c]
        else:
            text += '.'
    return text

# Convert a utf-8 or unicode text into a PDU string
def text_to_pdu(text):
    # If text not in unicode, convert/decode to unicode
    if not isinstance(text, unicode):
        text = str(text).decode('utf-8')
    # Get gsm code list for the text
    gsm_code = text_to_gsm_code(text)
    # Encode gsm code list in PDU
    # PDU encode consist in mount a 7-bit list of codes in 8-bit list,
    # but this string list is a hex representation of each 8-bit.
    # To the first 8-bit PDU code, put first 7-bit code, then complete
    # the left bit with the right bit of next code, so the second code
    # has now 6 bits.
    # Second, put the 6 bits and complete 2 left bits with the 2 right
    # bits of next 7-bit code. Now this has 5 bits.
    # Third, put the 5 bits and complete 3 left bits with the 3 right
    # bits of next 7-bit code. Now this has 4 bits.
    # Fourth, put the 4 bits and complete 4 left bits with the 4 right
    # bits of next 7-bit code. Now this has 3 bits.
    # Fifth, put the 3 bits and complete 5 left bits with the 5 right
    # bits of next 7-bit code. Now this has 2 bits.
    # Sixth, put the 2 bits and complete 6 left bits with the 6 right
    # bits of next 7-bit code. Now this has 1 bit.
    # Seventh, put the 1 bit and complete 7 left bits with the
    # next 7-bit code.
    # And so on until the end of 7-bits codes.
    # If the lenght of 7-bit code list is not multiple of 8, add plus
    # one PDU code with the remaining bits and zeros to the right
    pdu = ''
    i = 0
    for c in gsm_code:
        if not i: # start
            b = c
            i = 7
        else: # rest
            b = (c << i & 0xFF) + b
            pdu += "%02X" % b
            b = c >> (8 - i)
            i -= 1
    if len(gsm_code) % 8: # last
        pdu += "%02X" % b
    return pdu

# Convert a PDU string into a unicode text
def pdu_to_text(pdu, strip_at = True):
    gsm_code = []
    # Hex to int
    pdu_code = [int(pdu[i:i + 2], 16) for i in range(0, len(pdu), 2)]
    # Decode PDU in gsm code list, then return the unicode text 
    # PDU decode consist in extract a 7-bit list of codes in 8-bit list,
    # but this string list is a hex representation of each 8-bit.
    # First of all, get a list of integers from each 2 hex codes.
    # To the first 8-bit PDU code, the 7 right bits are the first 7-bit
    # code, and 1 left bit is to the next.
    # Second, the 6 bits right bits plus the 1 bit above, result the
    # second 7-bit code. 2 left bits is to the next
    # Third, the 5 bits right bits plus the 2 bits above, result the
    # third 7-bit code. 3 left bits is to the next
    # Fourth, the 4 bits right bits plus the 3 bits above, result the
    # fourth 7-bit code. 4 left bits is to the next
    # Fifth, the 3 bits right bits plus the 4 bits above, result the
    # fifth 7-bit code. 5 left bits is to the next
    # Sixth, the 2 bits right bits plus the 5 bits above, result the
    # sixth 7-bit code. 6 left bits is to the next
    # Seventh, the 1 bit right bits plus the 6 bits above, result the
    # seventh 7-bit code. 7 left bits is the eighth 7-bit code
    # And so on until the end.
    # One problem in it is when the last character is @ (0 in gsm code),
    # and the length of pdu is multiple of 14, it is impossible to know
    # if the string has or not @ at the end.
    i = 0
    for c in pdu_code:
        if not i:
            gsm_code.append(c & 0x7F)
        else:
            b = (c << i & 0x7F) + b
            gsm_code.append(b)
            if i == 6:
                gsm_code.append(c >> 1)
                i = -1
        b = c >> (7 - i)
        i += 1
    # Return the unicode text from gsm code, striped or not the last @
    text = gsm_code_to_text(gsm_code)
    if strip_at and len(pdu) % 14 == 0 and text[-1:] == '@':
        return text[:-1]
    return text

if __name__ == "__main__":
    print repr(pdu_to_text('D3309BFC0695DBA0B1BC4C4ED3DF7310B90C920A40B499CC059381EC61769AFC9E83C2F43228767BC16C2F192C367381866FF7BCCEA69741F3727D0E9A87D9E4F71C0497BFDBEF71FAED0EA7E72076FA1C7693DFA0B33C4CAFA7E9E176D94D2F8354359A6D04'))
    print '*144#', repr(text_to_pdu('*144#'))
    print '*544#', repr(text_to_pdu('*544#'))
    print '*546#', repr(text_to_pdu('*546#'))

    pdu = text_to_pdu('ABCDE[')
    print repr(pdu)
    print repr(pdu_to_text(pdu, False))

    pdu = text_to_pdu('@BCDEFG@')
    print repr(pdu)
    print repr(pdu_to_text(pdu))
    print repr(pdu_to_text(pdu, False))

    pdu = text_to_pdu('ABCDEFG$')
    print repr(pdu)
    print repr(pdu_to_text(pdu))
