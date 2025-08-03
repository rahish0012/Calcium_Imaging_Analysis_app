import streamlit as st
import pandas as pd

st.title("Calcium Imaging Analysis")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=None)
    # Read the uploaded Excel file without headers

    #Rename columns: odd = size, even = intensity
    renamed_cols = {}
    for i, col in enumerate(df.columns):
        neuron_index = i // 2 + 1 #specifying that neurons index start from 1
        #integer division to get the neuron index (1, 2, 3, ...)
        # For every two columns, the first one is size and the second one is area/intensity
        if i % 2 == 0:
            renamed_cols[col] = f"size_{neuron_index}" #the even indexed columns are size
        else:
            renamed_cols[col] = f"area_{neuron_index}" #odd ones are area/intensity
    df.rename(columns=renamed_cols, inplace=True) #rename the columns for further processing
    
    st.write("Data Preview:")
    st.dataframe(df.head(10))

    #Separate sizes and intensities
    size_cols = [col for col in df.columns if col.startswith("size_")]
    intensity_cols = [col for col in df.columns if col.startswith("area_")]

    size_df = df[size_cols]
    intensity_df = df[intensity_cols] 
    #subsetting the dataframe to only include size and intensity columns

   

    ### User input for start frames:
    st.write("Please enter the start frames for m-CPBG, Capcasin, and KCl:")
    # Start frames for Cap, KCl, and MC
    start_frame_mc = st.number_input("Enter start frame for m-CPBG", min_value=0)
    start_frame_cap = st.number_input("Enter start frame for Cap", min_value=0)
    start_frame_kcl = st.number_input("Enter start frame for KCl", min_value=0)
    
    #proceed only if the start frame are valid:

    if start_frame_cap > 0 and start_frame_kcl > 0 and start_frame_mc > 0:
        # 1. Compute global baseline
        baseline_mean = intensity_df.iloc[0:11].mean() #baseline mean will stay the same for all neurons
        #not calculating it again -- this is what caused the negative values 

        # 2. Compute global means from entire df
        mc_mean = intensity_df.iloc[start_frame_mc : start_frame_mc + 15].mean()
        cap_mean = intensity_df.iloc[start_frame_cap : start_frame_cap + 5].mean()
        kcl_mean = intensity_df.iloc[start_frame_kcl : start_frame_kcl + 5].mean()

        # 3. Define Cap responders
        #greater than 15% of baseline mean
        cap_mask = cap_mean > (baseline_mean * 1.15)
        cap_responder_cols = cap_mask[cap_mask].index.tolist()
        st.write("Cap responders:")
        st.dataframe(intensity_df.loc[start_frame_cap : start_frame_cap + 5, cap_responder_cols])


        # 4. Define MC responders
        #greater than 15% of baseline mean
        mc_mask = mc_mean > (baseline_mean * 1.15)
        mc_responder_cols = mc_mask[mc_mask].index.tolist()
        st.write("m-CPBG responder:")
        st.dataframe(intensity_df.loc[start_frame_mc : start_frame_mc + 15, mc_responder_cols])

        st.write("KCl window (for all neurons):")
        st.dataframe(intensity_df.loc[start_frame_kcl : start_frame_kcl + 5])

        st.write("Baseline window (for all neurons):")
        st.dataframe(intensity_df.loc[0:11])

        # Find overlapping responders between Cap and m-CPBG
        #shared_cols = list(set(cap_responder_cols) & set(mc_responder_cols))
        

        # --- Calculate normalized ratios for CAP responders ---
        if cap_responder_cols:
        # If there are overlapping responders, we need to ensure we only calculate ratios for unique responders
        
  

            # Calculate ΔF/F₀ using the same global means used in selection
            #this uses only the specified window. It does so by subsetting the mean values per neuron from the specified window
            mc_norm_cap = (mc_mean[cap_responder_cols] - baseline_mean[cap_responder_cols]) / baseline_mean[cap_responder_cols]
            #mc_norm_cap = mc_norm_cap.clip(lower=0) # Ensure non-negative values for ratios -- check with sarah
            cap_norm_cap = (cap_mean[cap_responder_cols] - baseline_mean[cap_responder_cols]) / baseline_mean[cap_responder_cols]
            kcl_norm_cap = (kcl_mean[cap_responder_cols] - baseline_mean[cap_responder_cols]) / baseline_mean[cap_responder_cols]

            # Combine into a DataFrame for display
            ff0_df_cap = pd.DataFrame({
                'Neuron': cap_responder_cols,
                'ΔF/F₀ (m-CPBG)': mc_norm_cap.values,
                'ΔF/F₀ (Cap)': cap_norm_cap.values,
                'ΔF/F₀ (KCl)': kcl_norm_cap.values
            })

            st.write("ΔF/F₀ values for Cap responders:")
            st.dataframe(ff0_df_cap.round(3))

            mc_cap_ratio = mc_norm_cap / cap_norm_cap #calculate the ratio of m-CPBG to Capcasin responders

            
            valid_mask = kcl_norm_cap > cap_norm_cap #identify where kcl is > than cap   
            mc_kcl_ratio_cap = (mc_norm_cap / kcl_norm_cap).where(valid_mask) #only calculate where kcl is greater than capcasin
            mc_kcl_ratio_cap = mc_kcl_ratio_cap[mc_kcl_ratio_cap >= 0] #keeping the ones that are greater than 0


            st.write(f"Capcasin responders (n = {len(cap_responder_cols)}):")
            #st.write("m-CPBG/cap ratio:", mc_cap_ratio.round(2))
            st.write("m-CPBG/KCl ratio (Cap responders):", mc_kcl_ratio_cap.round(2))

        # --- Calculate MC/KCl only for MC responders ---
        #this is not leading to any negative values -- 
        if mc_responder_cols:
            mc_norm_mc = (mc_mean[mc_responder_cols] - baseline_mean[mc_responder_cols]) / baseline_mean[mc_responder_cols]
            kcl_norm_mc = (kcl_mean[mc_responder_cols] - baseline_mean[mc_responder_cols]) / baseline_mean[mc_responder_cols]

            # Combine into a DataFrame for display
            ff0_df_mc = pd.DataFrame({
                'Neuron': mc_responder_cols,
                'ΔF/F₀ (m-CPBG)': mc_norm_mc.values,
                'ΔF/F₀ (KCl)': kcl_norm_mc.values
            })

            st.write("ΔF/F₀ values for m-CPBG responders:")
            st.dataframe(ff0_df_mc.round(3))

            mc_kcl_ratio_mc = mc_norm_mc / kcl_norm_mc
            mc_kcl_ratio_mc = mc_kcl_ratio_mc[mc_kcl_ratio_mc >= 0] #keep only the values that are greater than 0

            st.write(f"m-CPBG responders (n = {len(mc_responder_cols)}):")
            st.write("m-CPBG/KCl ratio (m-CPBG responders):", mc_kcl_ratio_mc.round(2))

        mc_nonresponder_cols = list(set(intensity_df.columns) - set(mc_responder_cols))
        #using set will make it the columns unique

        # Convert area_X to size_X
        mc_responder_size_cols = ['size_' + col.split('_')[1] for col in mc_responder_cols]
        mc_nonresponder_size_cols = ['size_' + col.split('_')[1] for col in mc_nonresponder_cols]

        # Subset size dataframe
        mc_responder_sizes = size_df[mc_responder_size_cols]
        mc_nonresponder_sizes = size_df[mc_nonresponder_size_cols]

        # Get average size across neurons
        #this gives the individual size for each neurons across all frames (it stays the same for all frames)

        avg_size_mc_responders = mc_responder_sizes.mean()
        avg_size_mc_nonresponders = mc_nonresponder_sizes.mean()

        st.write("Average size in m-CPBG responders:", avg_size_mc_responders)
        st.write("Average size in m-CPBG non-responders:", avg_size_mc_nonresponders)

        #finding overlap between cap and m-CPBG responders:

        import matplotlib.pyplot as plt
        from matplotlib_venn import venn2

        cap_set = set(cap_responder_cols)
        mc_set = set(mc_responder_cols)

        only_cap = cap_set - mc_set # Neurons that responded only to Cap
        only_mc = mc_set - cap_set # Neurons that responded only to m-CPBG
        # Neurons that responded to both Cap and m-CPBG
        both = cap_set & mc_set

        fig, ax = plt.subplots()
        venn2(subsets=(len(only_cap), len(only_mc), len(both)),
            set_labels=('Cap responders', 'm-CPBG responders'),
            ax=ax)
        st.pyplot(fig)


        shared_cols = list(set(cap_responder_cols) & set(mc_responder_cols))

        # Find overlapping responders between Cap and m-CPBG
