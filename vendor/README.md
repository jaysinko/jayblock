This directory vendors the Mozilla Public Suffix List:

https://publicsuffix.org/list/public_suffix_list.dat

License: MPL-2.0

The generator uses it to refuse public suffixes (com, github.io, amazonaws.com,
…) and to keep descendant collapsing inside a registrable namespace. Refresh
the file during a research pass; do not pull unofficial mirrors.
