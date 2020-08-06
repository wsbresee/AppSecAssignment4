#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "dictionary.h"

void remove_punctuation(char *word) {
    char *src = word;
    char *dst = word;
    for (; *src; ++src) {
        if (!ispunct((unsigned char) *src)) {
            *dst++ = tolower((unsigned char) *src);
        }
    }
    *dst = 0;
}

int check_words(FILE* fp, hashmap_t hashtable[], char* misspelled[]) {
    int num_misspelled = 0;
    char line[MAX_MISSPELLED];
    while (fgets(line, MAX_MISSPELLED, fp)) {
        char *word = strtok(line, " \"\t\n\v\f\r");
        while (word != NULL) {
            remove_punctuation(word);
            if (!check_word(word, hashtable)) {
                misspelled[num_misspelled] = strdup(word);
                num_misspelled++;
            }
            word = strtok(NULL, " \"\t\n\v\f\r");
        }
        free(word);
    }
    return num_misspelled;
}

bool load_dictionary(const char* dictionary_file, hashmap_t hashtable[]) {
    for(int i = 0; i < HASH_SIZE; i++) {
        hashtable[i] = NULL;
    }

    FILE* dictionary_pointer = fopen(dictionary_file, "r");
    hashmap_t new_node;

    if (dictionary_pointer == NULL) {
        return 0;
    }

    char word[LENGTH];
    while (fgets(word, LENGTH, dictionary_pointer) != NULL) {
        word[strcspn(word, " \"\t\n\v\f\r")] = 0;
        new_node = malloc(sizeof(struct node));
        new_node->next = NULL;
        strcpy(new_node->word, word);
        int bucket = hash_function(word);
        if (hashtable[bucket] == NULL) {
            hashtable[bucket] = new_node;
        } else {
            new_node->next = hashtable[bucket];
            hashtable[bucket] = new_node;
        }
    }
    fclose(dictionary_pointer);
    return 1;
}

char* lower_case(const char* word) {
    char *lower_case_word = malloc(strlen(word) * sizeof(char*));
    for (int i = 0; i < strlen(word); i++) {
        lower_case_word[i] = tolower(word[i]);
    }
    return lower_case_word;
}

bool check_word(const char* word, hashmap_t hashtable[]) {
    for (int i = 0; i < strlen(word); i++) {
        if (!isdigit(word[i])) {
            break;
        }
        if (i == strlen(word) - 1) {
            return 1;
        }
    }
    int bucket = hash_function(word);
    hashmap_t cursor = hashtable[bucket];
    while (cursor != NULL) {
        if (!strcmp(word, cursor->word)) {
            return 1;
        }
        cursor = cursor->next;
    }
    char *lower_case_word = lower_case(word);
    bucket = hash_function(lower_case_word);
    cursor = hashtable[bucket];
    while (cursor != NULL) {
        if (!strcmp(lower_case_word, cursor->word)) {
            free(lower_case_word);
            return 1;
        }
        cursor = cursor->next;
    }
    free(lower_case_word);
    return 0;
}
