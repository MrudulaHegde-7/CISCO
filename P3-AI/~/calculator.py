def add(first: float, second: float) -> float:
	return first + second


def subtract(first: float, second: float) -> float:
	return first - second


def multiply(first: float, second: float) -> float:
	return first * second


def divide(first: float, second: float) -> float:
	if second == 0:
		raise ZeroDivisionError("Cannot divide by zero.")
	return first / second


OPERATIONS = {
	"1": ("Add", add),
	"2": ("Subtract", subtract),
	"3": ("Multiply", multiply),
	"4": ("Divide", divide),
}


def main() -> None:
	while True:
		print("\nCalculator")
		print("1. Add  2. Subtract  3. Multiply  4. Divide  q. Quit")
		choice = input("Choose an operation: ").strip().lower()

		if choice == "q":
			print("Goodbye!")
			return
		if choice not in OPERATIONS:
			print("Invalid choice. Select 1, 2, 3, 4, or q.")
			continue

		try:
			first = float(input("Enter the first number: "))
			second = float(input("Enter the second number: "))
			name, operation = OPERATIONS[choice]
			result = operation(first, second)
		except ValueError:
			print("Please enter valid numbers.")
			continue
		except ZeroDivisionError as error:
			print(error)
			continue

		print(f"{name} result: {result:g}")


if __name__ == "__main__":
	main()
