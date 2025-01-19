package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"strings"

	"golang.design/x/clipboard"
)

type Job struct {
	text string
}

type Dictionary struct {
	English  string `json:"English"`
	Japanese string `json:"Japanese"`
}

var dictionary []Dictionary
var stats []Dictionary
var affixes []Dictionary

var parameter_pattern = regexp.MustCompile(`{\d(:[^}]+)?}`)

func main() {
	err := clipboard.Init()
	if err != nil {
		panic(err)
	}

	err = loadData()
	if err != nil {
		panic(err)
	}

	ch := make(chan Job, 10)
	go clipboard_watcher(ch)
	go translater(ch)

	fmt.Println("Watching clipboard...")
	fmt.Print("To exit, press Ctrl+C or type 'exit': ")
	var input string
	for {
		fmt.Scan(&input)
		if input == "exit" {
			close(ch)
			break
		}
	}
}

func clipboard_watcher(ch chan<- Job) {
	cpch := clipboard.Watch(context.TODO(), clipboard.FmtText)
	for data := range cpch {
		text := string(data)
		if isPOEItem(text) {
			ch <- Job{text: text}
		}
	}
}

func translater(ch <-chan Job) {
	for job := range ch {
		result := translate(job.text)
		clipboard.Write(clipboard.FmtText, []byte(result))
	}
}

func translate(text string) string {
	lines := splitLines(text)
	result := ""
	skipRarityNextDivider := false
	for _, line := range lines {
		if skipRarityNextDivider && strings.Contains(line, "--------") {
			skipRarityNextDivider = false
			continue
		}
		translated := translateLine(line)
		if strings.Contains(translated, "Rarity:") {
			skipRarityNextDivider = true
		}
		result += translated + "\n"
	}

	return result
}

func translateLine(line string) string {
	if strings.Contains(line, ": ") {
		// stats
		parts := strings.Split(line, ": ")
		return search_dict(parts[0]) + ": " + search_dict(parts[1])
	} else if strings.Contains(line, ":") {
		// label
		parts := strings.Split(line, ":")
		return search_dict(parts[0]) + ":"
	} else if strings.Contains(line, "--------") {
		// divider
		return line
	} else {
		// mods
		found := search_mods(line)
		if found != line {
			return found
		}
		// item category
		found = search_dict(line)
		if found != line {
			return found
		}
		// affix
		return search_affix(line)
	}
}

func search_dict(word string) string {
	for _, d := range dictionary {
		if d.Japanese == word {
			return d.English
		}
	}
	return word
}

func search_mods(word string) string {
	for _, s := range stats {
		pattern := s.Japanese
		pattern = strings.ReplaceAll(pattern, "[", "\\[")
		pattern = strings.ReplaceAll(pattern, "]", "\\]")
		params := parameter_pattern.FindAllStringSubmatch(pattern, -1)
		for i, param := range params {
			if len(param) > 1 && param[1] == ":+d" {
				pattern = strings.ReplaceAll(pattern, param[0], fmt.Sprintf("(?P<p%d>[+-]\\d+)", i+1))
			} else {
				pattern = strings.ReplaceAll(pattern, param[0], fmt.Sprintf("(?P<p%d>\\d+)", i+1))
			}
		}
		exp := regexp.MustCompile(pattern)
		result := exp.FindStringSubmatch(word)
		if result != nil {
			eng_text := s.English
			for i, param := range params {
				eng_text = strings.ReplaceAll(eng_text, param[0], result[i+1])
			}
			return eng_text
		}
	}
	return word
}

func search_affix(text string) string {
	var prefix *string = nil
	var suffix *string
	for _, af := range affixes {
		if strings.HasPrefix(text, af.Japanese) {
			prefix = &af.English
			break
		}
	}
	for _, af := range affixes {
		if strings.HasSuffix(text, af.Japanese) {
			suffix = &af.English
			break
		}
	}
	if prefix == nil || suffix == nil {
		return text
	}
	return *prefix + *suffix
}

func isPOEItem(text string) bool {
	return strings.Contains(text, "アイテムクラス")
}

func loadData() error {
	body, err := os.ReadFile("./data/dictionary.json")
	if err != nil {
		return err
	}

	err = json.Unmarshal(body, &dictionary)
	if err != nil {
		return err
	}

	body, err = os.ReadFile("./data/stats.json")
	if err != nil {
		return err
	}

	err = json.Unmarshal(body, &stats)
	if err != nil {
		return err
	}

	body, err = os.ReadFile("./data/words.json")
	if err != nil {
		return err
	}

	err = json.Unmarshal(body, &affixes)
	if err != nil {
		return err
	}

	return nil
}

func splitLines(text string) []string {
	var lines []string
	scanner := bufio.NewScanner(strings.NewReader(text))
	for scanner.Scan() {
		lines = append(lines, scanner.Text())
	}
	return lines
}
