// Supabase client
const supabaseClient = supabase.createClient(
  "https://mnbyvbhfkrkkmmgkedch.supabase.co",
  "sb_publishable_6Y-dqTHFSvMWoO-vcnqfiw_tvp9X3qB"
);

// College "Other" toggle
document.getElementById("college").addEventListener("change", function () {
  const otherInput = document.getElementById("otherCollege");

  if (this.value === "Other") {
    otherInput.classList.remove("hidden");
  } else {
    otherInput.classList.add("hidden");
  }
});

// ✅ FINAL PAYMENT FUNCTION (NO BACKEND)
async function handlePayment() {
  const btn = document.getElementById("payBtn");

  const data = {
    name: document.getElementById("name").value,
    phone: document.getElementById("phone").value,
    email: document.getElementById("email").value,
    city: document.getElementById("city").value,
    college: document.getElementById("college").value === "Other"
      ? document.getElementById("otherCollege").value
      : document.getElementById("college").value,
    course: document.getElementById("course").value,
    gender: document.getElementById("gender").value,
    requirements: document.getElementById("requirements").value,
  };

  // ✅ Validation
  if (!data.name || !data.phone || !data.email) {
    alert("Please fill required fields");
    return;
  }

  if (!/^\d{10}$/.test(data.phone)) {
    alert("Enter valid 10-digit phone number");
    return;
  }

  btn.innerText = "Redirecting...";
  btn.disabled = true;

  try {
    // ✅ Save to Supabase
    const { error } = await supabaseClient
      .from("booking_requests")
      .insert([{
        name: data.name,
        phone: data.phone,
        email: data.email,
        city: data.city,
        college: data.college,
        course: data.course,
        mentor_gender: data.gender,
        requirements: data.requirements,
        payment_id: "form_redirect",
        status: "pending"
      }]);

    if (error) {
      console.error("Supabase Error:", error);
      alert("Error saving data");
      btn.innerText = "Try Again";
      btn.disabled = false;
      return;
    }

    // ✅ Redirect to Cashfree Form
    window.location.href = "https://payments.cashfree.com/forms/eduronix-booking";

  } catch (err) {
    console.error("Error:", err);
    alert("Something went wrong");

    btn.innerText = "Try Again";
    btn.disabled = false;
  }
}