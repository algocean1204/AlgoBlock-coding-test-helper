package main

import "container/heap"

// Go에는 만들어진 힙이 없다. container/heap이 요구하는 메서드 다섯 개를 구현한다
// less 함수를 바꿔 끼우면 같은 타입으로 최소 힙과 최대 힙을 둘 다 만든다. 원소는 {높이, 번호}
type Heap struct {
	items [][2]int
	less  func(a, b [2]int) bool
}

func (h Heap) Len() int           { return len(h.items) }
func (h Heap) Less(i, j int) bool { return h.less(h.items[i], h.items[j]) }
func (h Heap) Swap(i, j int)      { h.items[i], h.items[j] = h.items[j], h.items[i] }
func (h *Heap) Push(x any)        { h.items = append(h.items, x.([2]int)) }
func (h *Heap) Pop() any {
	last := h.items[len(h.items)-1]
	h.items = h.items[:len(h.items)-1]
	return last
}

// 규칙 하나: 꼭대기를 보거나 꺼내기 전에는 언제나 이것을 부른다.
// 꼭대기에 창 밖으로 나간 판자(번호 < left)가 있으면 버린다. 힙 안쪽에 있는 것은 꼭대기에 올라올 때 버린다
func dropOld(h *Heap, left int) {
	for h.Len() > 0 && h.items[0][1] < left {
		heap.Pop(h)
	}
}

func solution(heights []int, w int) []int64 {
	n := len(heights)
	// low: 작은 쪽 절반. 높이가 큰 판자가 꼭대기에 오게 > 로 비교한다(부호를 뒤집는 대신 방향을 바꾼다)
	low := &Heap{less: func(a, b [2]int) bool {
		if a[0] != b[0] {
			return a[0] > b[0]
		}
		return a[1] < b[1]
	}}
	// high: 큰 쪽 절반. 높이가 낮은 판자가 꼭대기에 온다
	high := &Heap{less: func(a, b [2]int) bool {
		if a[0] != b[0] {
			return a[0] < b[0]
		}
		return a[1] < b[1]
	}}
	inLow := make([]bool, n) // 판자마다 지금 low에 들어 있는지
	lowCount, highCount := 0, 0 // 창 안에 남은 판자 수. 지울 표시만 한 판자가 힙에 남아 있어 Len()과 다르다
	lowSum, highSum := 0, 0     // Go의 int는 64비트라 넘치지 않는다
	left := 0                   // 창의 맨 왼쪽 번호. 이보다 작은 번호는 창 밖이다
	costs := []int64{}
	for right, height := range heights {
		// 1. 새 판자를 넣는다(4단계와 같다)
		dropOld(low, left)
		if low.Len() == 0 || height <= low.items[0][0] {
			heap.Push(low, [2]int{height, right})
			inLow[right] = true
			lowCount++
			lowSum += height
		} else {
			heap.Push(high, [2]int{height, right})
			highCount++
			highSum += height
		}
		// 2. 창이 w개를 넘으면 맨 왼쪽 판자를 뺀다. 힙에서 바로 지우지 않고 개수와 합에서만 뺀다
		if right-left+1 > w {
			if inLow[left] {
				lowCount--
				lowSum -= heights[left]
			} else {
				highCount--
				highSum -= heights[left]
			}
			left++
		}
		// 3. 개수 맞추기: lowCount가 highCount와 같거나 하나 더 많게. 옮기기 전에 꼭대기의 나간 판자를 버린다
		for lowCount > highCount+1 {
			dropOld(low, left)
			moved := heap.Pop(low).([2]int)
			heap.Push(high, moved)
			inLow[moved[1]] = false
			lowCount--
			lowSum -= moved[0]
			highCount++
			highSum += moved[0]
		}
		for highCount > lowCount {
			dropOld(high, left)
			moved := heap.Pop(high).([2]int)
			heap.Push(low, moved)
			inLow[moved[1]] = true
			highCount--
			highSum -= moved[0]
			lowCount++
			lowSum += moved[0]
		}
		// 4. 창이 w개로 찼으면 가운데 높이(low의 꼭대기)로 맞추는 비용을 잰다
		if right-left+1 == w {
			dropOld(low, left)
			middle := low.items[0][0]
			costs = append(costs, int64((middle*lowCount-lowSum)+(highSum-middle*highCount)))
		}
	}
	return costs
}
