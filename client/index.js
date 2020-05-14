const btn=document.getElementById("btn1");
const input_place=document.getElementById("place");
const input_days=document.getElementById("days");

const displayData=(data)=>{
    console.log(data)
}

const getResponse=async(data)=>{
    const formData = new FormData();
    formData.append('days',data.days);
    formData.append("location",data.place)

    const url="http://localhost:5000/generate";
    const config={
        method:"POST",
        body:formData
    }

    try{
        const response = await fetch(url,config)
        const data=await response.json()
        displayData(data)
    }
    catch(err){
        
    }
}

const TakeInput=(e)=>{
    e.preventDefault()
    if(input_days.value!=="" && input_place.value!==""){
        getResponse({place:input_place.value,days:input_days.value})
    }
    else{
        alert("Plese Provide all details...")
    }
}

btn.addEventListener("click",TakeInput)