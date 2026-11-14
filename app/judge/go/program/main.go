package main

import "fmt"

func main() {
	var count int
	fmt.Scan(&count)
	total := 0
	for index := 0; index < count; index++ {
		var value int
		fmt.Scan(&value)
		total += value
	}
	fmt.Println(total)
}
