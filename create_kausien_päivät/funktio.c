void* function(void* data, void* ret) {
    *(char*)ret = ((*(char*)data) == 5)*5;
    return ret;
}
