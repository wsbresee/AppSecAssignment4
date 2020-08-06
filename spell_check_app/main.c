#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "dictionary.h"

/*this function borrowed from online and modified*/
int main(int argc, char** argv) {
    hashmap_t hashtable[HASH_SIZE];
    FILE* fp = fopen(argv[1], "r");
    load_dictionary(argv[2], hashtable);
    char* misspelled[MAX_MISSPELLED];
    int num_misspelled = check_words(fp, hashtable, misspelled);
    printf("final misspelled words: ");
    for (int i = 0; i < num_misspelled; i++) {
        printf("%s\n", misspelled[i]);
    }
    for (int i = 0; i < num_misspelled; i++) {
        free(misspelled[i]);
    }
    for (int i = 0; i < HASH_SIZE; i++) {
        hashmap_t hashmap = hashtable[i];
        while (hashmap) {
            hashmap_t next_hashmap = hashmap->next;
            free(hashmap);
            hashmap = next_hashmap;
        }
    }
    fclose(fp);
}
