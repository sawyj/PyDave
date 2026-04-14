#include <stdlib.h>

#if (defined(_WIN32) || defined(_WIN64))
#define DAVE_EXPORT __declspec(dllexport)
#else
#define DAVE_EXPORT __attribute__((visibility("default")))
#endif

extern "C" DAVE_EXPORT void pydaveExternalSenderFree(void* ptr)
{
    free(ptr);
}
